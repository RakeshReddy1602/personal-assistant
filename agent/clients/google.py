import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
import threading

from dotenv import load_dotenv
try:
    from google.oauth2.credentials import Credentials  # type: ignore[import]
except Exception:  # pragma: no cover
    Credentials = Any  # type: ignore[assignment]
try:
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import]
except Exception:  # pragma: no cover
    InstalledAppFlow = Any  # type: ignore[assignment]
try:
    from googleapiclient.discovery import build  # type: ignore[import]
except Exception:  # pragma: no cover
    def build(*args: Any, **kwargs: Any) -> Any:  # type: ignore[no-redef]
        raise ImportError("googleapiclient not available")
try:
    from googleapiclient.errors import HttpError  # type: ignore[import]
except Exception:  # pragma: no cover
    class HttpError(Exception):  # type: ignore[no-redef]
        pass

load_dotenv()

# Scopes: Gmail + Calendar (single consent covers both)
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # Allows reading, sending, modifying, and deleting emails
    "https://www.googleapis.com/auth/calendar",
]


def _token_path() -> str:
    # Prefer explicit env var, else default to agent/token.pickle
    explicit = os.getenv("GOOGLE_TOKEN_FILE")
    if explicit:
        return explicit
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "token.pickle")


def _client_secret_path() -> str:
    path = os.getenv("GOOGLE_OAUTH_CLIENT_FILE")
    if not path:
        raise ValueError("Set GOOGLE_OAUTH_CLIENT_FILE (e.g., agent/oauth-creds.json)")
    path = os.path.abspath(os.path.expanduser('agent/'+path))
    if not os.path.exists(path):
        raise FileNotFoundError(f"OAuth client file not found: {path}")
    return path


_SERVICE_LOCK = threading.Lock()
_GMAIL_SERVICE: Any = None
_CALENDAR_SERVICE: Any = None


def init_gmail_service(force: bool = False) -> Any:
    global _GMAIL_SERVICE
    if _GMAIL_SERVICE is not None and not force:
        return _GMAIL_SERVICE
    with _SERVICE_LOCK:
        if _GMAIL_SERVICE is not None and not force:
            return _GMAIL_SERVICE
        creds: Optional[Credentials] = None
        token_file = _token_path()
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, scopes=GMAIL_SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    from google.auth.transport.requests import Request  # type: ignore[import]

                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds or not creds.valid:
                flow = InstalledAppFlow.from_client_secrets_file(_client_secret_path(), GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())

        _GMAIL_SERVICE = build("gmail", "v1", credentials=creds)
        return _GMAIL_SERVICE


def get_gmail_service() -> Any:
    if _GMAIL_SERVICE is None:
        return init_gmail_service()
    return _GMAIL_SERVICE


def init_calendar_service(force: bool = False) -> Any:
    global _CALENDAR_SERVICE
    # Ensure credentials exist (and token updated with unified scopes)
    init_gmail_service(force=False)
    if _CALENDAR_SERVICE is not None and not force:
        return _CALENDAR_SERVICE
    with _SERVICE_LOCK:
        if _CALENDAR_SERVICE is not None and not force:
            return _CALENDAR_SERVICE
        # Load credentials from the same token file; unified scopes avoid re-consent
        token_file = _token_path()
        creds = Credentials.from_authorized_user_file(token_file, scopes=GMAIL_SCOPES)  # type: ignore[call-arg]
        _CALENDAR_SERVICE = build("calendar", "v3", credentials=creds)
        return _CALENDAR_SERVICE


def get_calendar_service() -> Any:
    if _CALENDAR_SERVICE is None:
        return init_calendar_service()
    return _CALENDAR_SERVICE


def warmup_services(force: bool = False) -> None:
    """
    Optional eager initializer: ensures both Gmail and Calendar services are ready.
    Safe to call multiple times; thread-safe.
    """
    init_gmail_service(force=force)
    init_calendar_service(force=force)


def list_messages(
    query: Optional[str] = None,
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    service: Any = get_gmail_service()
    try:
        response = (
            service.users()  # type: ignore[attr-defined]
            .messages()
            .list(userId="me", q=query or "", maxResults=max_results, labelIds=label_ids or [])
            .execute()
        )
        messages = response.get("messages", [])
        results: List[Dict[str, Any]] = []
        for m in messages:
            msg = (
                service.users()  # type: ignore[attr-defined]
                .messages()
                .get(userId="me", id=m["id"], format="metadata")
                .execute()
            )
            headers = {h["name"].lower(): h.get("value", "") for h in msg.get("payload", {}).get("headers", [])}
            results.append(
                {
                    "id": msg.get("id"),
                    "threadId": msg.get("threadId"),
                    "snippet": msg.get("snippet"),
                    "internalDate": msg.get("internalDate"),
                    "from": headers.get("from", ""),
                    "to": headers.get("to", ""),
                    "subject": headers.get("subject", ""),
                    "date": headers.get("date", ""),
                }
            )
        return results
    except HttpError as e:
        raise RuntimeError(f"Gmail list_messages failed: {e}") from e


def send_message(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> Dict[str, Any]:
    service: Any = get_gmail_service()
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        sent = (
            service.users()  # type: ignore[attr-defined]
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        return {"id": sent.get("id"), "threadId": sent.get("threadId")}
    except HttpError as e:
        raise RuntimeError(f"Gmail send_message failed: {e}") from e
