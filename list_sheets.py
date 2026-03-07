"""List all sheets in the spreadsheet."""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from app.services.sheets_service import SheetsService
from app.core.config import settings
from loguru import logger

def main():
    """List all sheets."""
    print("=" * 80)
    print("SHEETS IN YOUR SPREADSHEET")
    print("=" * 80)
    print()
    
    try:
        sheets_service = SheetsService(settings.SHEETS_SPREADSHEET_ID)
        
        # Get spreadsheet metadata
        spreadsheet = sheets_service.service.spreadsheets().get(
            spreadsheetId=settings.SHEETS_SPREADSHEET_ID
        ).execute()
        
        sheets = spreadsheet.get('sheets', [])
        
        print(f"Found {len(sheets)} sheet(s):")
        print()
        
        for i, sheet in enumerate(sheets, 1):
            title = sheet['properties']['title']
            sheet_id = sheet['properties']['sheetId']
            print(f"{i}. {title} (ID: {sheet_id})")
        
        print()
        print("=" * 80)
        print()
        print("The bulk email data is in the 'EmailTracking' sheet.")
        print()
        print("If you don't see 'EmailTracking' in the list above,")
        print("it means the sheet wasn't created. Run:")
        print("  python initialize_email_tracking.py")
        print()
        print("Direct link to spreadsheet:")
        print(f"https://docs.google.com/spreadsheets/d/{settings.SHEETS_SPREADSHEET_ID}/edit")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
