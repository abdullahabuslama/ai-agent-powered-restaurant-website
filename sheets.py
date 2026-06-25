"""
sheets.py
---------
Google Sheets storage for reservations / customer contacts.

Authentication uses a local service-account `credentials.json` file. Every
reservation is appended as one row: [Timestamp, Name, Phone Number].

All functions are defensive: if Sheets is not configured or an error occurs,
they log the problem and return False instead of raising — so a storage issue
never breaks the live chat experience.
"""

import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

import config

logger = logging.getLogger(__name__)

# Scopes required to read/write the spreadsheet.
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_HEADER = ["Timestamp", "Name", "Phone Number"]

# Cache the worksheet handle so we don't re-authenticate on every message.
_worksheet = None


def _get_worksheet():
    """Authenticate (once) and return the target worksheet, ensuring a header row."""
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)

    # Use the configured tab, creating it if it doesn't exist yet.
    try:
        worksheet = spreadsheet.worksheet(config.GOOGLE_WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=config.GOOGLE_WORKSHEET_NAME, rows=1000, cols=10
        )

    # Ensure the header row exists exactly once. Note: gspread returns [] OR [[]]
    # (a single empty row) for a blank sheet, so check for actual content rather
    # than truthiness — otherwise the header would never be written.
    existing = worksheet.get_all_values()
    has_content = any(any((cell or "").strip() for cell in row) for row in existing)
    if not has_content:
        worksheet.append_row(_HEADER)

    _worksheet = worksheet
    return _worksheet


def append_reservation(name: str, phone: str) -> bool:
    """
    Append a reservation/contact row to the Google Sheet.

    Returns True on success, False on any failure (misconfiguration, auth error,
    network error, etc.). Failures are logged, never raised.
    """
    name = (name or "").strip()
    phone = (phone or "").strip()

    if not config.sheets_is_configured():
        logger.warning(
            "Google Sheets is not configured (missing GOOGLE_SHEET_ID or "
            "credentials.json). Reservation NOT saved: name=%r phone=%r",
            name,
            phone,
        )
        return False

    global _worksheet
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # The app caches one worksheet handle for its whole lifetime, so the
    # connection can go stale (Google drops idle keep-alive sockets) and the
    # first write fails with a transient "RemoteDisconnected"/"Connection
    # aborted" error. Retry once, dropping the cached handle so we reconnect
    # and re-authenticate fresh on the second attempt.
    last_exc = None
    for attempt in (1, 2):
        try:
            worksheet = _get_worksheet()
            # RAW (not USER_ENTERED) so phone numbers are stored verbatim as text.
            # USER_ENTERED makes Sheets parse "01000000000" as a number and drop
            # the leading zero, corrupting every local phone number.
            worksheet.append_row([timestamp, name, phone], value_input_option="RAW")
            logger.info("Reservation saved to Google Sheets: %s | %s", name, phone)
            return True
        except Exception as exc:  # noqa: BLE001 — storage must never crash the chat
            last_exc = exc
            logger.warning(
                "Sheets write attempt %d/2 failed (%s)%s",
                attempt,
                exc,
                "; reconnecting and retrying..." if attempt == 1 else ".",
            )
            _worksheet = None  # force a fresh connection on the next attempt

    logger.error("Failed to save reservation to Google Sheets: %s", last_exc)
    return False
