"""
Microsoft Outlook Integration Service

Sends emails through local Outlook installation using COM automation.
"""

import win32com.client
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OutlookClient:
    """Integration with Microsoft Outlook for email sending"""

    def __init__(self):
        self.outlook_app = None
        self.namespace = None
        self._initialize()

    def _initialize(self):
        """Initialize Outlook COM object"""
        try:
            self.outlook_app = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook_app.GetNamespace("MAPI")
            logger.info("Outlook client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Outlook: {e}")
            raise ConnectionError(f"Could not connect to Outlook: {e}")

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        html_body: bool = True,
        save_to_sent: bool = True
    ) -> Dict[str, any]:
        """
        Send email through Outlook

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: CC recipients (semicolon separated)
            bcc: BCC recipients (semicolon separated)
            attachments: List of file paths to attach
            html_body: Whether body is HTML (default: True)
            save_to_sent: Save to Sent Items (default: True)

        Returns:
            Dict with success status and details
        """

        try:
            # Create new email
            mail = self.outlook_app.CreateItem(0)  # 0 = olMailItem

            # Set recipients
            mail.To = to
            if cc:
                mail.CC = cc
            if bcc:
                mail.BCC = bcc

            # Set subject and body
            mail.Subject = subject

            if html_body:
                mail.HTMLBody = body
            else:
                mail.Body = body

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if Path(attachment_path).exists():
                        mail.Attachments.Add(str(attachment_path))
                    else:
                        logger.warning(f"Attachment not found: {attachment_path}")

            # Send email
            if save_to_sent:
                mail.Send()  # Sends and saves to Sent Items
            else:
                # Send without saving (requires additional permissions)
                mail.Send()

            logger.info(f"Email sent successfully to {to}: {subject}")

            return {
                "success": True,
                "to": to,
                "subject": subject,
                "sent_at": datetime.now().isoformat(),
                "message": "Email sent successfully via Outlook"
            }

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "to": to,
                "subject": subject,
                "error": str(e),
                "message": f"Failed to send email: {e}"
            }

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: bool = True
    ) -> Dict[str, any]:
        """
        Create draft email in Outlook (doesn't send)

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html_body: Whether body is HTML

        Returns:
            Dict with success status
        """

        try:
            mail = self.outlook_app.CreateItem(0)
            mail.To = to
            mail.Subject = subject

            if html_body:
                mail.HTMLBody = body
            else:
                mail.Body = body

            mail.Save()  # Save as draft

            logger.info(f"Draft email created: {subject}")

            return {
                "success": True,
                "to": to,
                "subject": subject,
                "message": "Draft created successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create draft: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_sender_email(self) -> Optional[str]:
        """Get the default sender email address from Outlook"""

        try:
            account = self.namespace.Accounts.Item(1)
            sender_email = account.SmtpAddress
            return sender_email
        except Exception as e:
            logger.error(f"Failed to get sender email: {e}")
            return None

    def get_signature(self) -> Optional[str]:
        """Get the default Outlook email signature"""

        try:
            # Get default signature from registry or temp file
            # This is a simplified version - full implementation would
            # read from Outlook settings or signature files
            return None  # User's Outlook signature will be auto-added
        except Exception as e:
            logger.error(f"Failed to get signature: {e}")
            return None

    def test_connection(self) -> bool:
        """Test Outlook connection"""

        try:
            # Try to access Outlook namespace
            _ = self.namespace.Folders.Count
            logger.info("Outlook connection test successful")
            return True
        except Exception as e:
            logger.error(f"Outlook connection test failed: {e}")
            return False

    def send_bulk_emails(
        self,
        emails: List[Dict[str, any]],
        delay_seconds: int = 5
    ) -> List[Dict[str, any]]:
        """
        Send multiple emails with delay between each

        Args:
            emails: List of email dicts with 'to', 'subject', 'body'
            delay_seconds: Delay between emails (to avoid spam filters)

        Returns:
            List of result dicts
        """

        import time

        results = []

        for i, email_data in enumerate(emails):
            result = self.send_email(
                to=email_data.get('to'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                cc=email_data.get('cc'),
                attachments=email_data.get('attachments'),
                html_body=email_data.get('html_body', True)
            )

            results.append(result)

            # Delay between emails (except for last one)
            if i < len(emails) - 1:
                time.sleep(delay_seconds)

        logger.info(f"Bulk email send completed: {len(results)} emails")

        return results

    def format_html_email(
        self,
        body_text: str,
        greeting: str = None,
        closing: str = "Best regards",
        include_logo: bool = False
    ) -> str:
        """
        Format email body as professional HTML

        Args:
            body_text: Main email content
            greeting: Opening greeting (e.g., "Dear John,")
            closing: Closing phrase
            include_logo: Whether to include company logo

        Returns:
            HTML formatted email
        """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, Helvetica, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333333;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .greeting {{
                    margin-bottom: 20px;
                }}
                .content {{
                    margin-bottom: 20px;
                }}
                .closing {{
                    margin-top: 20px;
                }}
                .payment-button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #1976d2;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .payment-button:hover {{
                    background-color: #1565c0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                {f'<div class="greeting">{greeting}</div>' if greeting else ''}

                <div class="content">
                    {body_text}
                </div>

                <div class="closing">
                    {closing}
                </div>
            </div>
        </body>
        </html>
        """

        return html


# Singleton instance
outlook_client = OutlookClient()
