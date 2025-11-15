from typing import Any, Dict, List, Optional, Union

from agent.mcp_servers.mail_mcp import services as mail_services


class _MailMcpServer:
    """
    Lightweight binder so we can use @mcp.tool(description=...) here without
    requiring a FastMCP instance at import-time. The orchestrator or main
    should call: tools.mcp.bind(actual_fastmcp_instance)
    """

    def __init__(self) -> None:
        self._mcp: Any = None
        self._pending: List[tuple] = []

    def bind(self, mcp: Any) -> None:
        self._mcp = mcp
        for func, kwargs in self._pending:
            mcp.tool(**kwargs)(func)
        self._pending.clear()

    def tool(self, description: Optional[str] = None) -> Any:
        def decorator(func: Any) -> Any:
            if self._mcp is not None:
                return self._mcp.tool(description=description)(func)
            self._pending.append((func, {"description": description}))
            return func

        return decorator


mcp = _MailMcpServer()


@mcp.tool(description="Read recent Gmail emails with optional query, labels, and time filters.")
def read_emails(
    query: str = "",
    max_results: int = 10,
    label_ids: List[str] = [],
    after_date: str = "",
    before_date: str = "",
    after_time: str = "",
    before_time: str = "",
) -> Dict[str, Any]:
    """
    Read recent Gmail messages with flexible filtering options.
    
    Supports Gmail search operators like from:, to:, subject:, has:attachment, etc.
    
    Time Filtering:
    - after_date: Show emails after date (YYYY/MM/DD format, e.g., "2024/01/15")
    - before_date: Show emails before date (YYYY/MM/DD format)
    - after_time: Show emails from last X time (e.g., "2h", "1d", "7d", "1w", "1m")
    - before_time: Show emails before X time ago
    
    Time format examples:
    - "2h" = last 2 hours
    - "1d" = last 1 day (24 hours)
    - "7d" = last 7 days (1 week)
    - "1w" = last 1 week
    - "1m" = last 1 month (30 days)
    
    Examples:
    - Get emails from last 24 hours: after_time="1d"
    - Get emails from last week: after_time="7d"
    - Get emails from specific date: after_date="2024/01/01"
    - Get emails in date range: after_date="2024/01/01", before_date="2024/01/31"
    """
    try:
        # Convert empty strings to None for optional parameters
        messages = mail_services.read_emails(
            query=query if query else None,
            max_results=max_results,
            label_ids=label_ids if label_ids else None,
            after_date=after_date if after_date else None,
            before_date=before_date if before_date else None,
            after_time=after_time if after_time else None,
            before_time=before_time if before_time else None
        )
        return {"messages": messages}
    except Exception as e:
        return {"error": f"Failed to read emails: {str(e)}"}


@mcp.tool(description="Get full email details including body and attachments.")
def get_email(message_id: str) -> Dict[str, Any]:
    """
    Get complete email details including full body content and attachment information.
    """
    try:
        email = mail_services.get_email(message_id=message_id)
        return email
    except Exception as e:
        return {"error": f"Failed to get email: {str(e)}"}


@mcp.tool(description="Send an email via Gmail with optional attachments.")
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
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
        attachments: List of file paths to attach (optional)
        html: Whether body is HTML (default: False)
    """
    try:
        result = mail_services.send_email(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc, 
            attachments=attachments, html=html
        )
        return {"sent": result}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


@mcp.tool(description="Create a draft email with optional attachments.")
def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    html: bool = False,
) -> Dict[str, Any]:
    """
    Create a draft email in Gmail.
    """
    try:
        result = mail_services.create_draft(
            to=to, subject=subject, body=body, cc=cc, bcc=bcc,
            attachments=attachments, html=html
        )
        return {"draft": result}
    except Exception as e:
        return {"error": f"Failed to create draft: {str(e)}"}


@mcp.tool(description="Reply to an email.")
def reply_to_email(
    message_id: str,
    body: str,
    html: bool = False,
) -> Dict[str, Any]:
    """
    Reply to an existing email message.
    """
    try:
        result = mail_services.reply_to_email(message_id=message_id, body=body, html=html)
        return {"sent": result}
    except Exception as e:
        return {"error": f"Failed to reply to email: {str(e)}"}


@mcp.tool(description="Forward an email to another recipient.")
def forward_email(
    message_id: str,
    to: str,
    body: str,
    html: bool = False,
) -> Dict[str, Any]:
    """
    Forward an existing email to another recipient.
    """
    try:
        result = mail_services.forward_email(message_id=message_id, to=to, body=body, html=html)
        return {"sent": result}
    except Exception as e:
        return {"error": f"Failed to forward email: {str(e)}"}


@mcp.tool(description="Delete an email by moving it to trash.")
def delete_email(message_id: str) -> Dict[str, Any]:
    """
    Delete an email by message ID (moves to trash).
    
    Args:
        message_id: The ID of the email message to delete
    """
    try:
        result = mail_services.delete_email(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete email: {str(e)}"}


@mcp.tool(description="Mark an email as read.")
def mark_email_read(message_id: str) -> Dict[str, Any]:
    """
    Mark an email as read.
    
    Args:
        message_id: The ID of the email message to mark as read
    """
    try:
        result = mail_services.mark_email_read(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to mark email as read: {str(e)}"}


@mcp.tool(description="Mark an email as unread.")
def mark_email_unread(message_id: str) -> Dict[str, Any]:
    """
    Mark an email as unread.
    
    Args:
        message_id: The ID of the email message to mark as unread
    """
    try:
        result = mail_services.mark_email_unread(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to mark email as unread: {str(e)}"}


@mcp.tool(description="Add labels to an email.")
def add_labels(message_id: str, label_ids: List[str]) -> Dict[str, Any]:
    """
    Add one or more labels to an email message.
    
    Args:
        message_id: The ID of the email message
        label_ids: List of label IDs to add
    """
    try:
        result = mail_services.add_labels(message_id=message_id, label_ids=label_ids)
        return result
    except Exception as e:
        return {"error": f"Failed to add labels: {str(e)}"}


@mcp.tool(description="Remove labels from an email.")
def remove_labels(message_id: str, label_ids: List[str]) -> Dict[str, Any]:
    """
    Remove one or more labels from an email message.
    
    Args:
        message_id: The ID of the email message
        label_ids: List of label IDs to remove
    """
    try:
        result = mail_services.remove_labels(message_id=message_id, label_ids=label_ids)
        return result
    except Exception as e:
        return {"error": f"Failed to remove labels: {str(e)}"}


@mcp.tool(description="List all Gmail labels.")
def list_labels() -> Dict[str, Any]:
    """
    List all available Gmail labels (both system and user labels).
    """
    try:
        labels = mail_services.list_labels()
        return {"labels": labels, "count": len(labels)}
    except Exception as e:
        return {"error": f"Failed to list labels: {str(e)}"}


@mcp.tool(description="Create a new Gmail label.")
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
    try:
        result = mail_services.create_label(
            name=name,
            label_list_visibility=label_list_visibility,
            message_list_visibility=message_list_visibility
        )
        return {"created": result}
    except Exception as e:
        return {"error": f"Failed to create label: {str(e)}"}


@mcp.tool(description="Update an existing Gmail label.")
def update_label(
    label_id: str,
    name: Optional[str] = None,
    label_list_visibility: Optional[str] = None,
    message_list_visibility: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing Gmail label.
    
    Args:
        label_id: The ID of the label to update
        name: New label name (optional)
        label_list_visibility: New visibility setting (optional)
        message_list_visibility: New message visibility (optional)
    """
    try:
        result = mail_services.update_label(
            label_id=label_id,
            name=name,
            label_list_visibility=label_list_visibility,
            message_list_visibility=message_list_visibility
        )
        return {"updated": result}
    except Exception as e:
        return {"error": f"Failed to update label: {str(e)}"}


@mcp.tool(description="Delete a Gmail label.")
def delete_label(label_id: str) -> Dict[str, Any]:
    """
    Delete a Gmail label.
    
    Args:
        label_id: The ID of the label to delete
    """
    try:
        result = mail_services.delete_label(label_id=label_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete label: {str(e)}"}


@mcp.tool(description="List all attachments in an email.")
def list_attachments(message_id: str) -> Dict[str, Any]:
    """
    List all attachments in an email message.
    
    Args:
        message_id: The ID of the email message
    """
    try:
        attachments = mail_services.list_attachments(message_id=message_id)
        return {"attachments": attachments, "count": len(attachments)}
    except Exception as e:
        return {"error": f"Failed to list attachments: {str(e)}"}


@mcp.tool(description="Download an email attachment to the local machine.")
def download_attachment(
    message_id: str,
    attachment_id: str,
    filename: str,
    save_path: str = "."
) -> Dict[str, Any]:
    """
    Download an email attachment and save it to disk.
    
    Args:
        message_id: The ID of the email message
        attachment_id: The ID of the attachment (get from list_attachments)
        filename: The name to save the file as
        save_path: Directory to save the file (default: current directory)
    """
    try:
        result = mail_services.download_attachment(
            message_id=message_id,
            attachment_id=attachment_id,
            filename=filename,
            save_path=save_path
        )
        return result
    except Exception as e:
        return {"error": f"Failed to download attachment: {str(e)}"}


@mcp.tool(description="Batch modify labels on multiple messages.")
def batch_modify_messages(
    message_ids: List[str],
    add_label_ids: Optional[List[str]] = None,
    remove_label_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Batch modify labels on multiple email messages at once.
    
    Args:
        message_ids: List of message IDs to modify
        add_label_ids: List of label IDs to add (optional)
        remove_label_ids: List of label IDs to remove (optional)
    """
    try:
        result = mail_services.batch_modify_messages(
            message_ids=message_ids,
            add_label_ids=add_label_ids,
            remove_label_ids=remove_label_ids
        )
        return result
    except Exception as e:
        return {"error": f"Failed to batch modify messages: {str(e)}"}
