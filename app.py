"""
app.py
------
The Streamlit web app: a modern, food-themed restaurant landing page with an
AI assistant in the sidebar.

Run with:  streamlit run app.py
"""

import streamlit as st

import config
from restaurant_data import RESTAURANT, GREETING
from chatbot import get_bot_response

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{RESTAURANT['name_en']} | {RESTAURANT['name_ar']}",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Styling — warm, food-themed (terracotta / cream / gold)
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;800&family=Poppins:wght@300;400;600&family=Cairo:wght@400;600;700&display=swap');

        :root {
            --terracotta: #C1502E;
            --terracotta-dark: #9E3D20;
            --cream: #FBF6EE;
            --gold: #D9A441;
            --charcoal: #2B2622;
            --olive: #5C6B3C;
        }

        .stApp { background: var(--cream); }

        /* Hide default Streamlit chrome for a cleaner site feel */
        #MainMenu, footer, header { visibility: hidden; }

        .block-container { padding-top: 1.5rem; max-width: 1100px; }

        /* ---------- Hero ---------- */
        .hero {
            background: linear-gradient(135deg, rgba(43,38,34,0.86), rgba(158,61,32,0.86)),
                        url('https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=80');
            background-size: cover;
            background-position: center;
            border-radius: 22px;
            padding: 4.5rem 2.5rem;
            text-align: center;
            color: #fff;
            margin-bottom: 2rem;
            box-shadow: 0 18px 40px rgba(43,38,34,0.25);
        }
        .hero h1 {
            font-family: 'Playfair Display', serif;
            font-size: 3.4rem;
            margin: 0;
            letter-spacing: 1px;
        }
        .hero .ar-name {
            font-family: 'Cairo', sans-serif;
            font-size: 1.9rem;
            color: var(--gold);
            margin-top: .2rem;
        }
        .hero p {
            font-family: 'Poppins', sans-serif;
            font-weight: 300;
            font-size: 1.15rem;
            margin-top: 1rem;
            opacity: .95;
        }
        .hero .ar-tag { font-family: 'Cairo', sans-serif; direction: rtl; }

        /* ---------- Section headings ---------- */
        .section-title {
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            color: var(--terracotta-dark);
            text-align: center;
            margin: 2.2rem 0 .3rem 0;
        }
        .section-sub {
            font-family: 'Cairo', sans-serif;
            text-align: center;
            color: var(--olive);
            font-size: 1.2rem;
            margin-bottom: 1.4rem;
            direction: rtl;
        }

        /* ---------- Cards ---------- */
        .card {
            background: #fff;
            border-radius: 16px;
            padding: 1.4rem 1.5rem;
            box-shadow: 0 8px 22px rgba(43,38,34,0.07);
            border: 1px solid rgba(217,164,65,0.25);
            height: 100%;
        }
        .card h3 {
            font-family: 'Poppins', sans-serif;
            color: var(--terracotta);
            margin: 0 0 .8rem 0;
            font-size: 1.15rem;
        }
        .card .row {
            display: flex;
            justify-content: space-between;
            padding: .35rem 0;
            border-bottom: 1px dashed rgba(0,0,0,0.08);
            font-family: 'Poppins', sans-serif;
            font-size: .95rem;
            color: var(--charcoal);
        }
        .card .row:last-child { border-bottom: none; }
        .card .price { color: var(--gold); font-weight: 600; white-space: nowrap; }

        /* ---------- Info / offers banner ---------- */
        .offer-banner {
            background: linear-gradient(135deg, var(--gold), #E8B85A);
            border-radius: 16px;
            padding: 1.3rem 1.6rem;
            color: var(--charcoal);
            font-family: 'Poppins', sans-serif;
            margin: .5rem 0;
            box-shadow: 0 8px 22px rgba(217,164,65,0.25);
        }
        .offer-banner b { color: var(--terracotta-dark); }

        .info-box {
            background:#fff; border-radius:16px; padding:1.4rem 1.6rem;
            box-shadow:0 8px 22px rgba(43,38,34,0.07);
            border-left:5px solid var(--terracotta);
            font-family:'Poppins',sans-serif; color:var(--charcoal);
            line-height:1.7; height:100%;
        }
        .info-box .ar { font-family:'Cairo',sans-serif; direction:rtl; color:var(--olive); }
        .info-box a { color: var(--terracotta); font-weight:600; text-decoration:none; }

        /* ---------- Sidebar (chat) ---------- */
        /* Chat takes ~40% of the page width and is ALWAYS visible (never collapses) */
        section[data-testid="stSidebar"] {
            background: #fff;
            width: 40vw !important;
            min-width: 360px !important;
            max-width: 40vw !important;
            /* Force the panel to stay on-screen even if Streamlit marks it "collapsed" */
            transform: none !important;
            margin-left: 0 !important;
            visibility: visible !important;
        }
        section[data-testid="stSidebar"] > div {
            width: 40vw !important;
            min-width: 360px !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: none !important;
            margin-left: 0 !important;
        }

        /* Remove the control that hides/collapses the chatbot — keep it always visible */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        button[kind="headerNoPadding"] {
            display: none !important;
        }
        .chat-header {
            background: linear-gradient(135deg, var(--terracotta), var(--terracotta-dark));
            color:#fff; border-radius:14px; padding:1rem 1.1rem; text-align:center;
            font-family:'Poppins',sans-serif; margin-bottom:.6rem;
        }
        .chat-header h2 { margin:0; font-size:1.25rem; color:#fff; }
        .chat-header span { font-size:.85rem; opacity:.9; color:#fff; }

        /* Keep chat text dark & readable regardless of the visitor's theme */
        section[data-testid="stSidebar"] [data-testid="stChatMessage"] {
            background: #FBF6EE;
            border: 1px solid rgba(217,164,65,0.25);
            border-radius: 14px;
            padding: .55rem .7rem;
            margin-bottom: .4rem;
        }
        section[data-testid="stSidebar"] [data-testid="stChatMessage"] p,
        section[data-testid="stSidebar"] [data-testid="stChatMessage"] li,
        section[data-testid="stSidebar"] [data-testid="stChatMessage"] strong {
            color: var(--charcoal) !important;
        }

        .footer {
            text-align:center; color:var(--olive); font-family:'Poppins',sans-serif;
            padding:2.5rem 0 1rem 0; font-size:.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Landing page sections
# ---------------------------------------------------------------------------
def render_hero():
    r = RESTAURANT
    st.markdown(
        f"""
        <div class="hero">
            <h1>{r['name_en']}</h1>
            <div class="ar-name">{r['name_ar']}</div>
            <p>{r['tagline_en']}</p>
            <p class="ar-tag">{r['tagline_ar']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_about():
    r = RESTAURANT
    st.markdown('<div class="section-title">Our Story</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">قصتنا</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="info-box">{r["about_en"]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'<div class="info-box"><span class="ar">{r["about_ar"]}</span></div>',
            unsafe_allow_html=True,
        )


def render_offers():
    r = RESTAURANT
    st.markdown('<div class="section-title">Weekly Offers</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">عروض الأسبوع</div>', unsafe_allow_html=True)
    for offer in r["offers"]:
        st.markdown(
            f'<div class="offer-banner">🎉 <b>{offer["en"]}</b><br>'
            f'<span style="font-family:Cairo,sans-serif;direction:rtl;display:block;">{offer["ar"]}</span></div>',
            unsafe_allow_html=True,
        )


def render_menu():
    r = RESTAURANT
    st.markdown('<div class="section-title">Our Menu</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">قائمة الطعام</div>', unsafe_allow_html=True)

    categories = list(r["menu"].items())
    # Two cards per row.
    for i in range(0, len(categories), 2):
        cols = st.columns(2)
        for col, (category, items) in zip(cols, categories[i:i + 2]):
            rows = "".join(
                f'<div class="row"><span>{it["en"]} · {it["ar"]}</span>'
                f'<span class="price">{it["price"]}</span></div>'
                for it in items
            )
            col.markdown(
                f'<div class="card"><h3>{category}</h3>{rows}</div>',
                unsafe_allow_html=True,
            )
        st.write("")


def render_info():
    r = RESTAURANT
    st.markdown('<div class="section-title">Hours, Location & Delivery</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">المواعيد، الموقع، والتوصيل</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""<div class="info-box">
            <h3 style="color:var(--terracotta);margin-top:0;">🕒 Working Hours</h3>
            {r['hours_en']}
            <div class="ar" style="margin-top:.6rem;">{r['hours_ar']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="info-box">
            <h3 style="color:var(--terracotta);margin-top:0;">📍 Location</h3>
            {r['address_en']}
            <div class="ar" style="margin-top:.6rem;">{r['address_ar']}</div>
            <div style="margin-top:.7rem;"><a href="{r['maps_url']}" target="_blank">🗺️ Open in Google Maps</a></div>
            <div style="margin-top:.4rem;">📞 {r['phone']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="info-box">
            <h3 style="color:var(--terracotta);margin-top:0;">🛵 Delivery</h3>
            {r['delivery_en']}
            <div class="ar" style="margin-top:.6rem;">{r['delivery_ar']}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_footer():
    r = RESTAURANT
    st.markdown(
        f"""<div class="footer">
        🌿 {r['name_en']} · {r['name_ar']} &nbsp;|&nbsp; 📞 {r['phone']} &nbsp;|&nbsp; ✉️ {r['email']}<br>
        Ask our AI assistant anything in the chat → &nbsp;·&nbsp; اسأل مساعدنا الذكي في الدردشة ←
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar chat assistant
# ---------------------------------------------------------------------------
def init_state():
    if "messages" not in st.session_state:
        # Display messages: list of {"role": "user"|"assistant", "text": str}
        st.session_state.messages = [{"role": "assistant", "text": GREETING}]
    if "history" not in st.session_state:
        # Provider-neutral conversation history: list of {"role", "content"} dicts.
        st.session_state.history = []


def render_chat():
    with st.sidebar:
        st.markdown(
            f"""<div class="chat-header">
            <h2>🌿 {RESTAURANT['name_en']} Assistant</h2>
            <span>مساعد {RESTAURANT['name_ar']} · Ask me anything!</span>
            </div>""",
            unsafe_allow_html=True,
        )

        if not config.chatbot_is_configured():
            st.warning(
                "⚠️ The assistant isn't connected yet. Add your GROQ_API_KEY (or "
                "GEMINI_API_KEY) to the .env file.\n\nالمساعد غير مفعّل بعد — أضف مفتاح "
                "GROQ_API_KEY (أو GEMINI_API_KEY) في ملف .env."
            )

        # Render the conversation so far.
        for msg in st.session_state.messages:
            avatar = "🧑" if msg["role"] == "user" else "🌿"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["text"])

        # Input box (pinned at the bottom of the sidebar).
        prompt = st.chat_input("Type your message... / اكتب رسالتك...")
        if prompt:
            handle_user_message(prompt)


def handle_user_message(prompt: str):
    # Record the user's message, generate the reply, then rerun so the whole
    # conversation (including these new messages) is redrawn ABOVE the input box.
    # Rendering inline here would place new messages below the chat input.
    st.session_state.messages.append({"role": "user", "text": prompt})

    with st.spinner("..."):
        reply, updated_history = get_bot_response(prompt, st.session_state.history)

    # Persist state for the next turn.
    st.session_state.history = updated_history
    st.session_state.messages.append({"role": "assistant", "text": reply})
    st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()
    init_state()

    # Sidebar assistant.
    render_chat()

    # Main landing page.
    render_hero()
    render_about()
    render_offers()
    render_menu()
    render_info()
    render_footer()


if __name__ == "__main__":
    main()
