from typing import Any, Dict, List, Optional

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


@mcp.tool(description="Read recent Gmail emails with optional query and labels.")
def read_emails(
    query: Optional[str] = None,
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Read recent Gmail messages matching an optional query and labels.
    """
    try:
        messages = mail_services.read_emails(query=query, max_results=max_results, label_ids=label_ids)
        return {"messages": messages}
    except Exception as e:
        return {"error": f"Failed to read emails: {str(e)}"}


@mcp.tool(description="Send an email via Gmail.")
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email via Gmail.
    """
    try:
        result = mail_services.send_email(to=to, subject=subject, body=body, cc=cc, bcc=bcc)
        return {"sent": result}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


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


