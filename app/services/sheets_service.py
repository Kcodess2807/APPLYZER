"""Google Sheets service for tracking applications."""
from typing import List, Dict, Any, Optional
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.core.sheets_auth import get_sheets_credentials
from app.core.config import settings


class SheetsService:
    """Google Sheets API service wrapper."""
    
    HEADERS = [
        "Company", "HR Email", "Job Role", "Date Sent", "Email Status",
        "Message ID", "Thread ID", "Reply Received", "Last Follow Up",
        "Follow Up Count", "Notes"
    ]
    
    def __init__(self, spreadsheet_id: Optional[str] = None):
        """Initialize Sheets service."""
        self.creds = get_sheets_credentials()
        if not self.creds or not self.creds.valid:
            raise ValueError("Sheets not authenticated. Please run: python initialize_email_tracking.py")
        
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = spreadsheet_id or settings.SHEETS_SPREADSHEET_ID
    
    def create_tracker_sheet(self, title: str = "Job Applications Tracker") -> str:
        """Create new tracking spreadsheet."""
        try:
            spreadsheet = {
                'properties': {'title': title},
                'sheets': [{
                    'properties': {'title': 'Applications'},
                    'data': [{
                        'startRow': 0,
                        'startColumn': 0,
                        'rowData': [{
                            'values': [{'userEnteredValue': {'stringValue': h}} for h in self.HEADERS]
                        }]
                    }]
                }]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result['spreadsheetId']
            
            logger.info(f"Created tracker sheet: {spreadsheet_id}")
            return spreadsheet_id
            
        except HttpError as error:
            logger.error(f"Error creating sheet: {error}")
            raise
    
    def add_application(self, application_data: Dict[str, Any]) -> int:
        """Add application row to sheet."""
        try:
            values = [[
                application_data.get('company', ''),
                application_data.get('hr_email', ''),
                application_data.get('job_role', ''),
                application_data.get('date_sent', datetime.now().strftime('%Y-%m-%d %H:%M')),
                application_data.get('status', 'SENT'),
                application_data.get('message_id', ''),
                application_data.get('thread_id', ''),
                application_data.get('reply_received', 'FALSE'),
                application_data.get('last_followup', ''),
                application_data.get('followup_count', 0),
                application_data.get('notes', '')
            ]]
            
            body = {'values': values}
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Applications!A:K',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Get row number
            updated_range = result.get('updates', {}).get('updatedRange', '')
            row_num = int(updated_range.split('!')[1].split(':')[0][1:])
            
            logger.info(f"Added application to row {row_num}")
            return row_num
            
        except HttpError as error:
            logger.error(f"Error adding application: {error}")
            raise
    
    def update_application(self, row: int, updates: Dict[str, Any]):
        """Update application row."""
        try:
            # Map column names to indices
            col_map = {h: i for i, h in enumerate(self.HEADERS)}
            
            for field, value in updates.items():
                if field in col_map:
                    col_letter = chr(65 + col_map[field])  # A=65
                    range_name = f'Applications!{col_letter}{row}'
                    
                    body = {'values': [[value]]}
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption='USER_ENTERED',
                        body=body
                    ).execute()
            
            logger.info(f"Updated row {row}")
            
        except HttpError as error:
            logger.error(f"Error updating row: {error}")
            raise
    
    def get_applications(self) -> List[Dict[str, Any]]:
        """Get all applications from sheet."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Applications!A2:K'
            ).execute()
            
            rows = result.get('values', [])
            
            applications = []
            for i, row in enumerate(rows, start=2):
                if len(row) >= len(self.HEADERS):
                    app = {
                        'row': i,
                        'company': row[0],
                        'hr_email': row[1],
                        'job_role': row[2],
                        'date_sent': row[3],
                        'status': row[4],
                        'message_id': row[5],
                        'thread_id': row[6],
                        'reply_received': row[7],
                        'last_followup': row[8],
                        'followup_count': int(row[9]) if row[9] else 0,
                        'notes': row[10]
                    }
                    applications.append(app)
            
            return applications
            
        except HttpError as error:
            logger.error(f"Error getting applications: {error}")
            return []
    
    def mark_reply_received(self, row: int):
        """Mark application as replied."""
        self.update_application(row, {
            'Reply Received': 'TRUE',
            'Email Status': 'REPLIED'
        })
