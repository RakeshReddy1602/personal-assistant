"""
Mail MCP Server

A FastMCP server that exposes Gmail tools via HTTP.
Run this server separately, and the orchestrator will connect to it.
"""

from fastmcp import FastMCP
from typing import Optional, List
from agent.mcp_servers.mail_mcp import services

# Initialize FastMCP server
mcp = FastMCP('Mail Server')


@mcp.tool(description="Read recent Gmail emails with optional query and labels.")
def read_emails(
    query: Optional[str] = None,
    max_results: int = 10,
    label_ids: Optional[List[str]] = None,
) -> dict:
    """
    Read recent Gmail messages matching an optional query and labels.
    
    Args:
        query: Search query (optional)
        max_results: Maximum number of emails to return
        label_ids: List of label IDs to filter by (optional)
    
    Returns:
        dict: Dictionary containing list of messages
    """
    try:
        messages = services.read_emails(query=query, max_results=max_results, label_ids=label_ids)
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
) -> dict:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        cc: CC recipients (optional)
        bcc: BCC recipients (optional)
    
    Returns:
        dict: Sent email information
    """
    try:
        result = services.send_email(to=to, subject=subject, body=body, cc=cc, bcc=bcc)
        return {"sent": result}
    except Exception as e:
        return {"error": f"Failed to send email: {str(e)}"}


@mcp.tool(description="Delete an email by moving it to trash.")
def delete_email(message_id: str) -> dict:
    """
    Delete an email by message ID (moves to trash).
    
    Args:
        message_id: The ID of the email message to delete
    
    Returns:
        dict: Deletion confirmation
    """
    try:
        result = services.delete_email(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to delete email: {str(e)}"}


@mcp.tool(description="Mark an email as read.")
def mark_email_read(message_id: str) -> dict:
    """
    Mark an email as read.
    
    Args:
        message_id: The ID of the email message to mark as read
    
    Returns:
        dict: Update confirmation
    """
    try:
        result = services.mark_email_read(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to mark email as read: {str(e)}"}


@mcp.tool(description="Mark an email as unread.")
def mark_email_unread(message_id: str) -> dict:
    """
    Mark an email as unread.
    
    Args:
        message_id: The ID of the email message to mark as unread
    
    Returns:
        dict: Update confirmation
    """
    try:
        result = services.mark_email_unread(message_id=message_id)
        return result
    except Exception as e:
        return {"error": f"Failed to mark email as unread: {str(e)}"}


@mcp.tool(description="List all attachments in an email.")
def list_attachments(message_id: str) -> dict:
    """
    List all attachments in an email message.
    
    Args:
        message_id: The ID of the email message
    
    Returns:
        dict: List of attachments with metadata
    """
    try:
        attachments = services.list_attachments(message_id=message_id)
        return {"attachments": attachments, "count": len(attachments)}
    except Exception as e:
        return {"error": f"Failed to list attachments: {str(e)}"}


@mcp.tool(description="Download an email attachment to the local machine.")
def download_attachment(
    message_id: str,
    attachment_id: str,
    filename: str,
    save_path: str = "."
) -> dict:
    """
    Download an email attachment and save it to disk.
    
    Args:
        message_id: The ID of the email message
        attachment_id: The ID of the attachment (get from list_attachments)
        filename: The name to save the file as
        save_path: Directory to save the file (default: current directory)
    
    Returns:
        dict: Download confirmation with file path
    """
    try:
        result = services.download_attachment(
            message_id=message_id,
            attachment_id=attachment_id,
            filename=filename,
            save_path=save_path
        )
        return result
    except Exception as e:
        return {"error": f"Failed to download attachment: {str(e)}"}


# Run the server when this file is executed directly
if __name__ == "__main__":
    print("Starting Mail MCP Server on http://127.0.0.1:6281/mcp")
    mcp.run(transport="http", host="127.0.0.1", port=6281, stateless_http=True)

