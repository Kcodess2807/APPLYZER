"""Gmail service for sending and reading emails."""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.core.gmail_auth import get_gmail_credentials


class GmailService:
    """Gmail API service wrapper."""
    
    def __init__(self):
        """Initialize Gmail service."""
        self.creds = get_gmail_credentials()
        if not self.creds:
            raise ValueError("Gmail not authenticated")
        
        self.service = build('gmail', 'v1', credentials=self.creds)
    
    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None
    ) -> dict:
        """Send email with attachments."""
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            
            msg_html = MIMEText(body_html, 'html')
            message.attach(msg_html)
            
            if attachments:
                for file_path in attachments:
                    self._attach_file(message, file_path)
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent to {to}. Message ID: {send_result['id']}")
            
            return {
                'success': True,
                'message_id': send_result['id'],
                'thread_id': send_result['threadId']
            }
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return {'success': False, 'error': str(error)}
    
    def _attach_file(self, message: MIMEMultipart, file_path: str):
        """Attach file to email."""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Attachment not found: {file_path}")
            return
        
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={path.name}')
        message.attach(part)
    
    def check_thread_replies(self, thread_id: str) -> bool:
        """Check if thread has replies."""
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages = thread.get('messages', [])
            return len(messages) > 1
            
        except HttpError as error:
            logger.error(f"Error checking thread: {error}")
            return False
    
    def list_messages(self, query: str = '', max_results: int = 10) -> List[dict]:
        """List messages matching query."""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            return results.get('messages', [])
            
        except HttpError as error:
            logger.error(f"Error listing messages: {error}")
            return []
