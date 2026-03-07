"""Service for tracking emails in Google Sheets."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.services.sheets_service import SheetsService
from app.core.config import settings


class EmailTrackerService:
    """Service for managing email tracking in Google Sheets."""
    
    # Updated headers for bulk email tracking
    HEADERS = [
        "email", "subject", "thread_id", "status", 
        "sent_at", "followup_count", "message_id", "last_checked"
    ]
    
    def __init__(self, spreadsheet_id: Optional[str] = None):
        """Initialize email tracker service."""
        self.sheets_service = SheetsService(spreadsheet_id)
        self.spreadsheet_id = spreadsheet_id or settings.SHEETS_SPREADSHEET_ID
    
    def add_email_tracking(
        self,
        email: str,
        subject: str,
        thread_id: str,
        message_id: str,
        status: str = "SENT"
    ) -> int:
        """Add email tracking entry to sheet."""
        try:
            sent_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            values = [[
                email,
                subject,
                thread_id,
                status,
                sent_at,
                0,  # followup_count
                message_id,
                sent_at  # last_checked
            ]]
            
            body = {'values': values}
            
            result = self.sheets_service.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='EmailTracking!A:H',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Extract row number
            updated_range = result.get('updates', {}).get('updatedRange', '')
            if updated_range:
                row_num = int(updated_range.split('!')[1].split(':')[0][1:])
                logger.info(f"Added email tracking for {email} at row {row_num}")
                return row_num
            
            return -1
            
        except Exception as error:
            logger.error(f"Error adding email tracking: {error}")
            raise
    
    def get_emails_by_status(self, status: str = "SENT") -> List[Dict[str, Any]]:
        """Get all emails with specific status."""
        try:
            result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='EmailTracking!A2:H'
            ).execute()
            
            rows = result.get('values', [])
            
            emails = []
            for i, row in enumerate(rows, start=2):
                if len(row) >= 4 and row[3] == status:
                    email_data = {
                        'row': i,
                        'email': row[0] if len(row) > 0 else '',
                        'subject': row[1] if len(row) > 1 else '',
                        'thread_id': row[2] if len(row) > 2 else '',
                        'status': row[3] if len(row) > 3 else '',
                        'sent_at': row[4] if len(row) > 4 else '',
                        'followup_count': int(row[5]) if len(row) > 5 and row[5] else 0,
                        'message_id': row[6] if len(row) > 6 else '',
                        'last_checked': row[7] if len(row) > 7 else ''
                    }
                    emails.append(email_data)
            
            logger.info(f"Found {len(emails)} emails with status {status}")
            return emails
            
        except Exception as error:
            logger.error(f"Error getting emails by status: {error}")
            return []
    
    def get_emails_for_followup(self) -> List[Dict[str, Any]]:
        """
        Get emails that need follow-up.
        
        Returns emails where:
        - Status is "SENT" (no reply received)
        - Sent more than FOLLOWUP_DAYS_INTERVAL days ago
        - followup_count < MAX_FOLLOWUP_COUNT
        """
        try:
            result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='EmailTracking!A2:H'
            ).execute()
            
            rows = result.get('values', [])
            
            if not rows:
                logger.info("No email tracking data found")
                return []
            
            followup_threshold = datetime.now() - timedelta(days=settings.FOLLOWUP_DAYS_INTERVAL)
            
            emails = []
            for i, row in enumerate(rows, start=2):
                # Skip rows with insufficient data
                if len(row) < 6:
                    logger.debug(f"Skipping row {i}: insufficient data")
                    continue
                
                try:
                    status = row[3] if len(row) > 3 else ''
                    sent_at_str = row[4] if len(row) > 4 else ''
                    followup_count_str = row[5] if len(row) > 5 else '0'
                    
                    # Parse followup count safely
                    try:
                        followup_count = int(followup_count_str) if followup_count_str else 0
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid followup_count in row {i}: {followup_count_str}")
                        followup_count = 0
                    
                    # Check if email needs follow-up
                    if status == "SENT" and followup_count < settings.MAX_FOLLOWUP_COUNT:
                        # Parse and validate sent_at date
                        if not sent_at_str:
                            logger.warning(f"Row {i} has no sent_at date, skipping")
                            continue
                        
                        try:
                            sent_at = datetime.strptime(sent_at_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            logger.warning(f"Invalid date format in row {i}: {sent_at_str}")
                            continue
                        
                        # Check if enough time has passed
                        if sent_at < followup_threshold:
                            email_data = {
                                'row': i,
                                'email': row[0] if len(row) > 0 else '',
                                'subject': row[1] if len(row) > 1 else '',
                                'thread_id': row[2] if len(row) > 2 else '',
                                'status': status,
                                'sent_at': sent_at_str,
                                'followup_count': followup_count,
                                'message_id': row[6] if len(row) > 6 else ''
                            }
                            
                            # Validate required fields
                            if email_data['email'] and email_data['thread_id']:
                                emails.append(email_data)
                            else:
                                logger.warning(f"Row {i} missing email or thread_id, skipping")
                
                except Exception as row_error:
                    logger.error(f"Error processing row {i}: {row_error}")
                    continue
            
            logger.info(f"Found {len(emails)} emails needing follow-up (threshold: {followup_threshold.strftime('%Y-%m-%d %H:%M:%S')})")
            return emails
            
        except Exception as error:
            logger.error(f"Error getting emails for follow-up: {error}", exc_info=True)
            raise
    
    def update_email_status(self, row: int, status: str):
        """Update email status."""
        try:
            range_name = f'EmailTracking!D{row}'
            body = {'values': [[status]]}
            
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Update last_checked
            last_checked_range = f'EmailTracking!H{row}'
            last_checked_body = {'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]}
            
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=last_checked_range,
                valueInputOption='USER_ENTERED',
                body=last_checked_body
            ).execute()
            
            logger.info(f"Updated email status to {status} for row {row}")
            
        except Exception as error:
            logger.error(f"Error updating email status: {error}")
            raise
    
    def increment_followup_count(self, row: int):
        """
        Increment follow-up count and update sent_at timestamp.
        
        Args:
            row: Row number in the EmailTracking sheet
        """
        try:
            if row < 2:
                raise ValueError(f"Invalid row number: {row}. Must be >= 2")
            
            # Get current followup_count
            range_name = f'EmailTracking!F{row}'
            result = self.sheets_service.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            current_count = 0
            values = result.get('values', [])
            if values and values[0]:
                try:
                    current_count = int(values[0][0]) if values[0][0] else 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid followup_count in row {row}, resetting to 0")
                    current_count = 0
            
            new_count = current_count + 1
            
            # Validate against max count
            if new_count > settings.MAX_FOLLOWUP_COUNT:
                logger.warning(f"Row {row} exceeds MAX_FOLLOWUP_COUNT ({settings.MAX_FOLLOWUP_COUNT})")
            
            # Update followup_count
            body = {'values': [[new_count]]}
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Update sent_at to current time
            sent_at_range = f'EmailTracking!E{row}'
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sent_at_body = {'values': [[current_time]]}
            
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=sent_at_range,
                valueInputOption='USER_ENTERED',
                body=sent_at_body
            ).execute()
            
            # Update last_checked timestamp
            last_checked_range = f'EmailTracking!H{row}'
            last_checked_body = {'values': [[current_time]]}
            
            self.sheets_service.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=last_checked_range,
                valueInputOption='USER_ENTERED',
                body=last_checked_body
            ).execute()
            
            logger.info(f"Incremented follow-up count to {new_count} for row {row}")
            
        except Exception as error:
            logger.error(f"Error incrementing follow-up count for row {row}: {error}", exc_info=True)
            raise
    
    def create_tracking_sheet(self):
        """Create EmailTracking sheet if it doesn't exist."""
        try:
            # Check if sheet exists
            spreadsheet = self.sheets_service.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_exists = any(
                sheet['properties']['title'] == 'EmailTracking' 
                for sheet in sheets
            )
            
            if not sheet_exists:
                # Create new sheet
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': 'EmailTracking'
                            }
                        }
                    }]
                }
                
                self.sheets_service.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request_body
                ).execute()
                
                # Add headers
                header_body = {'values': [self.HEADERS]}
                self.sheets_service.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='EmailTracking!A1:H1',
                    valueInputOption='USER_ENTERED',
                    body=header_body
                ).execute()
                
                logger.info("Created EmailTracking sheet with headers")
            else:
                logger.info("EmailTracking sheet already exists")
                
        except Exception as error:
            logger.error(f"Error creating tracking sheet: {error}")
            raise
