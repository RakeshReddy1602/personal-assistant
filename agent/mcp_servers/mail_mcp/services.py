import base64
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from agent.clients.google import init_gmail_service

_SERVICE_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {"service": None}


def initialize_mail_service(force: bool = False) -> Any:
    if _STATE["service"] is not None and not force:
        return _STATE["service"]
    with _SERVICE_LOCK:
        if _STATE["service"] is not None and not force:
            return _STATE["service"]
        _STATE["service"] = init_gmail_service(force=force)
        return _STATE["service"]


def _get_service() -> Any:
    if _STATE["service"] is None:
        return initialize_mail_service()
    return _STATE["service"]


def read_emails(
    query: Optional[str] = None,
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    service: Any = _get_service()
    response = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .list(userId="me", q=query or "", maxResults=max_results, labelIds=label_ids or [])
        .execute()
    )
    messages = response.get("messages", []) if isinstance(response, dict) else []
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


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> Dict[str, Any]:
    service: Any = _get_service()
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return {"id": sent.get("id"), "threadId": sent.get("threadId")}


def delete_email(message_id: str) -> Dict[str, Any]:
    """
    Delete an email by message ID (moves to trash).
    """
    service: Any = _get_service()
    service.users().messages().trash(userId="me", id=message_id).execute()  # type: ignore[attr-defined]
    return {"deleted": True, "messageId": message_id}


def mark_email_read(message_id: str) -> Dict[str, Any]:
    """
    Mark an email as read by removing the UNREAD label.
    """
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    return {"marked": "read", "messageId": message_id, "success": True, "response": result}


def mark_email_unread(message_id: str) -> Dict[str, Any]:
    """
    Mark an email as unread by adding the UNREAD label.
    """
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"addLabelIds": ["UNREAD"]}
    ).execute()
    return {"marked": "unread", "messageId": message_id, "success": True, "response": result}


def download_attachment(message_id: str, attachment_id: str, filename: str, save_path: str = ".") -> Dict[str, Any]:
    """
    Download an email attachment and save it to disk.
    
    Args:
        message_id: The ID of the email message
        attachment_id: The ID of the attachment
        filename: The name to save the file as
        save_path: Directory to save the file (default: current directory)
    """
    import os
    
    service: Any = _get_service()
    
    # Get the attachment
    attachment = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=attachment_id)
        .execute()
    )
    
    # Decode the attachment data
    file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))
    
    # Create the full file path
    full_path = os.path.join(save_path, filename)
    
    # Write the file
    with open(full_path, "wb") as f:
        f.write(file_data)
    
    return {
        "downloaded": True,
        "filename": filename,
        "path": full_path,
        "size": len(file_data)
    }


def list_attachments(message_id: str) -> List[Dict[str, Any]]:
    """
    List all attachments in an email message.
    
    Args:
        message_id: The ID of the email message
    
    Returns:
        List of attachments with their IDs, filenames, and sizes
    """
    service: Any = _get_service()
    
    # Get the full message
    message = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    
    attachments = []
    
    def extract_attachments(parts: List[Dict[str, Any]]) -> None:
        for part in parts:
            if part.get("filename"):
                body = part.get("body", {})
                if body.get("attachmentId"):
                    attachments.append({
                        "attachmentId": body["attachmentId"],
                        "filename": part["filename"],
                        "mimeType": part.get("mimeType", ""),
                        "size": body.get("size", 0)
                    })
            
            # Recursively check for nested parts
            if "parts" in part:
                extract_attachments(part["parts"])
    
    payload = message.get("payload", {})
    if "parts" in payload:
        extract_attachments(payload["parts"])
    
    return attachments


