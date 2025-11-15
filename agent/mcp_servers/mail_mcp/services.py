import base64
import mimetypes
import os
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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


def _extract_email_body(payload: Dict[str, Any]) -> str:
    """Extract email body from payload, handling multipart messages."""
    body = ""
    
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
            elif mime_type == "text/html" and not body:
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                body = _extract_email_body(part)
                if body:
                    break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    
    return body


def _build_time_query(
    after_date: Optional[str] = None,
    before_date: Optional[str] = None,
    after_time: Optional[str] = None,
    before_time: Optional[str] = None,
) -> str:
    """
    Build time-based query string for Gmail.
    
    Args:
        after_date: Date in format YYYY/MM/DD or relative like "1d" (1 day ago)
        before_date: Date in format YYYY/MM/DD
        after_time: Time filter (e.g., "2h" for 2 hours ago, "1d" for 1 day ago)
        before_time: Time filter
    
    Returns:
        Query string for Gmail search
    """
    from datetime import datetime, timedelta
    
    query_parts = []
    
    # Handle after_date
    if after_date:
        query_parts.append(f"after:{after_date}")
    
    # Handle before_date
    if before_date:
        query_parts.append(f"before:{before_date}")
    
    # Handle after_time (relative time like "2h", "1d", "7d")
    if after_time:
        # Parse relative time format
        unit = after_time[-1]
        value = int(after_time[:-1])
        
        if unit == 'h':  # hours
            delta = timedelta(hours=value)
        elif unit == 'd':  # days
            delta = timedelta(days=value)
        elif unit == 'w':  # weeks
            delta = timedelta(weeks=value)
        elif unit == 'm':  # months (approximate as 30 days)
            delta = timedelta(days=value * 30)
        else:
            delta = timedelta(days=value)
        
        target_date = datetime.now() - delta
        formatted_date = target_date.strftime("%Y/%m/%d")
        query_parts.append(f"after:{formatted_date}")
    
    # Handle before_time
    if before_time:
        unit = before_time[-1]
        value = int(before_time[:-1])
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        elif unit == 'w':
            delta = timedelta(weeks=value)
        elif unit == 'm':
            delta = timedelta(days=value * 30)
        else:
            delta = timedelta(days=value)
        
        target_date = datetime.now() - delta
        formatted_date = target_date.strftime("%Y/%m/%d")
        query_parts.append(f"before:{formatted_date}")
    
    return " ".join(query_parts)


def read_emails(
    query: Optional[str] = None,
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
    after_date: Optional[str] = None,
    before_date: Optional[str] = None,
    after_time: Optional[str] = None,
    before_time: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Read recent Gmail messages matching an optional query and labels with time filtering.
    
    Args:
        query: Gmail search query
        max_results: Maximum number of results (default: 10)
        label_ids: Filter by label IDs
        after_date: Show emails after this date (YYYY/MM/DD format)
        before_date: Show emails before this date (YYYY/MM/DD format)
        after_time: Show emails after relative time (e.g., "2h", "1d", "7d", "1w")
        before_time: Show emails before relative time (e.g., "2h", "1d", "7d")
    
    Time formats:
        - "2h" = 2 hours ago
        - "1d" = 1 day ago
        - "7d" = 7 days ago (1 week)
        - "1w" = 1 week ago
        - "1m" = 1 month ago (30 days)
    """
    service: Any = _get_service()
    
    # Build complete query with time filters
    time_query = _build_time_query(after_date, before_date, after_time, before_time)
    
    # Combine user query with time query
    complete_query = query or ""
    if time_query:
        complete_query = f"{complete_query} {time_query}".strip()
    
    response = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .list(userId="me", q=complete_query, maxResults=max_results, labelIds=label_ids or [])
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
                "labelIds": msg.get("labelIds", []),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
            }
        )
    return results


def get_email(message_id: str) -> Dict[str, Any]:
    """Get full email details including body and attachments."""
    service: Any = _get_service()
    
    message = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    
    headers = {h["name"].lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}
    
    # Extract email body
    body = _extract_email_body(message.get("payload", {}))
    
    # Get attachments info
    attachments = []
    
    def extract_attachments(parts: List[Dict[str, Any]]) -> None:
        for part in parts:
            if part.get("filename"):
                body_data = part.get("body", {})
                if body_data.get("attachmentId"):
                    attachments.append({
                        "attachmentId": body_data["attachmentId"],
                        "filename": part["filename"],
                        "mimeType": part.get("mimeType", ""),
                        "size": body_data.get("size", 0)
                    })
            if "parts" in part:
                extract_attachments(part["parts"])
    
    payload = message.get("payload", {})
    if "parts" in payload:
        extract_attachments(payload["parts"])
    
    return {
        "id": message.get("id"),
        "threadId": message.get("threadId"),
        "labelIds": message.get("labelIds", []),
        "snippet": message.get("snippet"),
        "internalDate": message.get("internalDate"),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "bcc": headers.get("bcc", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "body": body,
        "attachments": attachments
    }


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False,
) -> Dict[str, Any]:
    """
    Send an email via Gmail with optional attachments.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        attachments: List of file paths to attach (optional)
        html: Whether body is HTML (default: False)
    """
    service: Any = _get_service()
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    
    # Add body
    msg.attach(MIMEText(body, "html" if html else "plain"))
    
    # Add attachments
    if attachments:
        for file_path in attachments:
            if not os.path.exists(file_path):
                continue
            
            filename = os.path.basename(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type is None:
                mime_type = "application/octet-stream"
            
            main_type, sub_type = mime_type.split("/", 1)
            
            with open(file_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return {"id": sent.get("id"), "threadId": sent.get("threadId")}


def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False,
) -> Dict[str, Any]:
    """Create a draft email."""
    service: Any = _get_service()
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = subject
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    
    msg.attach(MIMEText(body, "html" if html else "plain"))
    
    # Add attachments
    if attachments:
        for file_path in attachments:
            if not os.path.exists(file_path):
                continue
            
            filename = os.path.basename(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type is None:
                mime_type = "application/octet-stream"
            
            main_type, sub_type = mime_type.split("/", 1)
            
            with open(file_path, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = (
        service.users()  # type: ignore[attr-defined]
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return {"id": draft.get("id"), "message": draft.get("message", {})}


def reply_to_email(
    message_id: str,
    body: str,
    html: bool = False,
) -> Dict[str, Any]:
    """Reply to an email."""
    service: Any = _get_service()
    
    # Get original message
    original = service.users().messages().get(userId="me", id=message_id, format="full").execute()  # type: ignore
    headers = {h["name"].lower(): h.get("value", "") for h in original.get("payload", {}).get("headers", [])}
    
    # Create reply
    msg = MIMEMultipart()
    msg["to"] = headers.get("from", "")
    msg["subject"] = "Re: " + headers.get("subject", "")
    msg["In-Reply-To"] = headers.get("message-id", "")
    msg["References"] = headers.get("references", "") + " " + headers.get("message-id", "")
    
    msg.attach(MIMEText(body, "html" if html else "plain"))
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .send(userId="me", body={"raw": raw, "threadId": original.get("threadId")})
        .execute()
    )
    return {"id": sent.get("id"), "threadId": sent.get("threadId")}


def forward_email(
    message_id: str,
    to: str,
    body: str,
    html: bool = False,
) -> Dict[str, Any]:
    """Forward an email."""
    service: Any = _get_service()
    
    # Get original message
    original = service.users().messages().get(userId="me", id=message_id, format="full").execute()  # type: ignore
    headers = {h["name"].lower(): h.get("value", "") for h in original.get("payload", {}).get("headers", [])}
    
    # Create forward
    msg = MIMEMultipart()
    msg["to"] = to
    msg["subject"] = "Fwd: " + headers.get("subject", "")
    
    msg.attach(MIMEText(body, "html" if html else "plain"))
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = (
        service.users()  # type: ignore[attr-defined]
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return {"id": sent.get("id"), "threadId": sent.get("threadId")}


def delete_email(message_id: str) -> Dict[str, Any]:
    """Delete an email by message ID (moves to trash)."""
    service: Any = _get_service()
    service.users().messages().trash(userId="me", id=message_id).execute()  # type: ignore[attr-defined]
    return {"deleted": True, "messageId": message_id}


def mark_email_read(message_id: str) -> Dict[str, Any]:
    """Mark an email as read by removing the UNREAD label."""
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    return {"marked": "read", "messageId": message_id, "success": True, "response": result}


def mark_email_unread(message_id: str) -> Dict[str, Any]:
    """Mark an email as unread by adding the UNREAD label."""
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"addLabelIds": ["UNREAD"]}
    ).execute()
    return {"marked": "unread", "messageId": message_id, "success": True, "response": result}


def add_labels(message_id: str, label_ids: List[str]) -> Dict[str, Any]:
    """Add labels to an email."""
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"addLabelIds": label_ids}
    ).execute()
    return {"messageId": message_id, "labelsAdded": label_ids, "success": True}


def remove_labels(message_id: str, label_ids: List[str]) -> Dict[str, Any]:
    """Remove labels from an email."""
    service: Any = _get_service()
    result = service.users().messages().modify(  # type: ignore[attr-defined]
        userId="me",
        id=message_id,
        body={"removeLabelIds": label_ids}
    ).execute()
    return {"messageId": message_id, "labelsRemoved": label_ids, "success": True}


def list_labels() -> List[Dict[str, Any]]:
    """List all Gmail labels."""
    service: Any = _get_service()
    results = service.users().labels().list(userId="me").execute()  # type: ignore[attr-defined]
    labels = results.get("labels", [])
    return labels


def create_label(
    name: str,
    label_list_visibility: str = "labelShow",
    message_list_visibility: str = "show"
) -> Dict[str, Any]:
    """
    Create a new Gmail label.
    
    Args:
        name: Label name
        label_list_visibility: labelShow, labelShowIfUnread, or labelHide
        message_list_visibility: show or hide
    """
    service: Any = _get_service()
    label = {
        "name": name,
        "labelListVisibility": label_list_visibility,
        "messageListVisibility": message_list_visibility
    }
    result = service.users().labels().create(userId="me", body=label).execute()  # type: ignore[attr-defined]
    return result


def update_label(
    label_id: str,
    name: Optional[str] = None,
    label_list_visibility: Optional[str] = None,
    message_list_visibility: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing label."""
    service: Any = _get_service()
    label = {}
    if name:
        label["name"] = name
    if label_list_visibility:
        label["labelListVisibility"] = label_list_visibility
    if message_list_visibility:
        label["messageListVisibility"] = message_list_visibility
    
    result = service.users().labels().patch(userId="me", id=label_id, body=label).execute()  # type: ignore[attr-defined]
    return result


def delete_label(label_id: str) -> Dict[str, Any]:
    """Delete a label."""
    service: Any = _get_service()
    service.users().labels().delete(userId="me", id=label_id).execute()  # type: ignore[attr-defined]
    return {"deleted": True, "labelId": label_id}


def download_attachment(message_id: str, attachment_id: str, filename: str, save_path: str = ".") -> Dict[str, Any]:
    """Download an email attachment and save it to disk."""
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
    """List all attachments in an email message."""
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


def batch_modify_messages(
    message_ids: List[str],
    add_label_ids: Optional[List[str]] = None,
    remove_label_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Batch modify labels on multiple messages."""
    service: Any = _get_service()
    
    body = {
        "ids": message_ids,
        "addLabelIds": add_label_ids or [],
        "removeLabelIds": remove_label_ids or []
    }
    
    service.users().messages().batchModify(userId="me", body=body).execute()  # type: ignore[attr-defined]
    
    return {
        "success": True,
        "modifiedCount": len(message_ids),
        "addedLabels": add_label_ids or [],
        "removedLabels": remove_label_ids or []
    }
