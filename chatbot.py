"""
chatbot.py
----------
The brain of the assistant. Multi-provider with a seamless fallback chain:

    Groq (PRIMARY)            Gemini (FALLBACK)
    ┌─────────────────┐       ┌────────────────┐
    │ GROQ_MODEL_1    │  ──►   │ MODEL_GEMINI_1 │  ──►  friendly error
    │ GROQ_MODEL_2    │        │ MODEL_GEMINI_2 │
    └─────────────────┘       └────────────────┘

Responsibilities:
  1. ROBUST FALLBACK — try each provider/model in order. Any failure (rate limit,
     quota, permission denied, network, empty reply...) logs a warning and moves to
     the next model. The customer never sees an error; only if EVERY model fails do
     we return a friendly bilingual message.
  2. RESERVATION CAPTURE — expose a `save_reservation` tool that the model calls once
     it has collected the customer's name + phone. We execute it ourselves so we keep
     full control of the loop, and it works identically across both providers.

Conversation history is kept in a PROVIDER-NEUTRAL format — a plain list of
{"role": "user"|"assistant", "content": str} turns. Each provider converts that to
its own native format at call time and runs its own tool-call loop internally, so a
fallback can happen at any turn without corrupting the running conversation.
"""

import json
import logging

import config
import sheets
from restaurant_data import build_system_prompt

logger = logging.getLogger(__name__)

# Max generate→tool→generate iterations per turn (safety net against tool loops).
_MAX_TOOL_TURNS = 5

# Friendly bilingual message shown only if EVERY provider/model fails completely.
_HARD_FAILURE_MESSAGE = (
    "😊 Sorry, I'm having a brief hiccup right now. Please try again in a moment, or "
    "call us directly.\n\n"
    "😊 عذراً، تواجهني مشكلة بسيطة الآن. من فضلك حاول مرة أخرى بعد قليل، أو اتصل بنا مباشرة."
)

# Single source of truth for the reservation tool, described once in a
# provider-neutral way. Each provider adapter renders it into its own schema.
_TOOL_NAME = "save_reservation"
_TOOL_DESCRIPTION = (
    "Save a customer's reservation or contact details. Call this ONLY after you have "
    "collected BOTH the customer's full name AND their phone number."
)
_TOOL_PROPERTIES = {
    "name": {"type": "string", "description": "The customer's full name."},
    "phone": {
        "type": "string",
        "description": "The customer's phone number (with any country code they gave).",
    },
}
_TOOL_REQUIRED = ["name", "phone"]


# ---------------------------------------------------------------------------
# Shared tool execution (provider-agnostic)
# ---------------------------------------------------------------------------
def _execute_function(name: str, args: dict) -> dict:
    """Run a tool the model asked for and return a JSON-serialisable result payload."""
    if name == _TOOL_NAME:
        customer_name = (args.get("name") or "").strip()
        phone = (args.get("phone") or "").strip()
        saved = sheets.append_reservation(customer_name, phone)
        if saved:
            return {
                "status": "success",
                "message": f"Reservation saved for {customer_name} ({phone}).",
            }
        return {
            "status": "error",
            "message": (
                "Could not save to the system right now. Politely reassure the customer "
                "that you've noted their details and the team will contact them, and "
                "offer the restaurant phone number."
            ),
        }

    logger.warning("Model requested unknown function: %s", name)
    return {"status": "error", "message": f"Unknown function '{name}'."}


# ===========================================================================
# Provider: Groq (PRIMARY) — OpenAI-compatible chat completions + tool calling
# ===========================================================================
_groq_client = None

# Groq / OpenAI-style tool schema.
_GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": _TOOL_NAME,
            "description": _TOOL_DESCRIPTION,
            "parameters": {
                "type": "object",
                "properties": _TOOL_PROPERTIES,
                "required": _TOOL_REQUIRED,
            },
        },
    }
]


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq  # imported lazily so the app starts even without the SDK

        _groq_client = Groq(api_key=config.GROQ_API_KEY)
    return _groq_client


def _groq_chat(convo, model) -> str:
    """
    Run one full reply (with an internal tool-call loop) using a Groq model.

    `convo` is the provider-neutral history plus the current user turn. Returns the
    final assistant text. Raises on any API error so the caller can fall back.
    """
    client = _get_groq_client()

    # Build the working message list: system instruction + the conversation so far.
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages.extend({"role": m["role"], "content": m["content"]} for m in convo)

    for _ in range(_MAX_TOOL_TURNS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=_GROQ_TOOLS,
            temperature=0.7,
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            return (message.content or "").strip()

        # Record the assistant's tool-call turn, then execute each tool.
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _execute_function(tc.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                }
            )

    logger.error("Groq '%s' exceeded the tool-call loop without a final reply.", model)
    return ""


# ===========================================================================
# Provider: Gemini (FALLBACK) — google-genai with manual function calling
# ===========================================================================
_gemini_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai  # lazy import

        _gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _gemini_client


def _gemini_config():
    """Generation config: persona/system instruction + reservation tool."""
    from google.genai import types

    declaration = types.FunctionDeclaration(
        name=_TOOL_NAME,
        description=_TOOL_DESCRIPTION,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                key: types.Schema(type=types.Type.STRING, description=prop["description"])
                for key, prop in _TOOL_PROPERTIES.items()
            },
            required=_TOOL_REQUIRED,
        ),
    )
    return types.GenerateContentConfig(
        system_instruction=build_system_prompt(),
        tools=[types.Tool(function_declarations=[declaration])],
        temperature=0.7,
        # We handle function execution ourselves to control the loop.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def _gemini_chat(convo, model) -> str:
    """
    Run one full reply (with an internal tool-call loop) using a Gemini model.

    Converts the provider-neutral history into google-genai `Content` objects.
    Returns the final assistant text. Raises on any API error.
    """
    from google.genai import types

    # Convert neutral history -> Gemini contents (user -> "user", assistant -> "model").
    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in convo
    ]

    client = _get_gemini_client()
    cfg = _gemini_config()

    for _ in range(_MAX_TOOL_TURNS):
        response = client.models.generate_content(
            model=model, contents=contents, config=cfg
        )
        candidate = response.candidates[0] if response.candidates else None
        parts = (candidate.content.parts if candidate and candidate.content else None) or []
        function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

        if candidate and candidate.content:
            contents.append(candidate.content)

        if not function_calls:
            return (response.text or "").strip()

        tool_response_parts = []
        for fc in function_calls:
            result = _execute_function(fc.name, dict(fc.args or {}))
            tool_response_parts.append(
                types.Part.from_function_response(name=fc.name, response=result)
            )
        contents.append(types.Content(role="user", parts=tool_response_parts))

    logger.error("Gemini '%s' exceeded the tool-call loop without a final reply.", model)
    return ""


# ===========================================================================
# Public entry point
# ===========================================================================
def _provider_chain():
    """Ordered list of (kind, model) pairs to try: all Groq first, then all Gemini."""
    chain = []
    if config.groq_is_configured():
        for model in (config.GROQ_MODEL_1, config.GROQ_MODEL_2):
            if model:
                chain.append(("groq", model))
    if config.gemini_is_configured():
        for model in (config.MODEL_GEMINI_1, config.MODEL_GEMINI_2):
            if model:
                chain.append(("gemini", model))
    return chain


def get_bot_response(user_message: str, history):
    """
    Generate the assistant's reply to `user_message`.

    `history` is the provider-neutral conversation (list of {"role", "content"} dicts;
    empty on the first message). Returns (reply_text, updated_history).
    Never raises — on total failure it returns a friendly bilingual message and leaves
    history unchanged.
    """
    convo = list(history) + [{"role": "user", "content": user_message}]

    chain = _provider_chain()
    if not chain:
        logger.error("No chatbot provider configured (no GROQ_API_KEY or GEMINI_API_KEY).")
        return _HARD_FAILURE_MESSAGE, history

    runners = {"groq": _groq_chat, "gemini": _gemini_chat}
    last_error = None

    for index, (kind, model) in enumerate(chain):
        try:
            text = runners[kind](convo, model)
            if not text:
                raise RuntimeError("empty response")
            if index > 0:
                logger.info("Fallback model '%s/%s' answered successfully.", kind, model)
            updated = convo + [{"role": "assistant", "content": text}]
            return text, updated
        except Exception as exc:  # noqa: BLE001 — broad on purpose: any failure -> next model
            last_error = exc
            is_last = index == len(chain) - 1
            level = logger.error if is_last else logger.warning
            level(
                "Model '%s/%s' failed (%s). %s",
                kind,
                model,
                exc,
                "No more fallbacks available." if is_last else "Falling back to next model...",
            )

    logger.error("get_bot_response failed completely: %s", last_error)
    return _HARD_FAILURE_MESSAGE, history
