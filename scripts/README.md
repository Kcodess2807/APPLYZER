# ApplyBot Utility Scripts

This directory contains utility scripts for setup, authentication, and testing.

## Authentication Scripts

### `authenticate_apis.sh`
Bash script to authenticate both Gmail and Google Sheets APIs in one command.

```bash
./scripts/authenticate_apis.sh
```

### `authenticate_sheets.py`
Python script to authenticate Google Sheets API and save credentials.

```bash
python scripts/authenticate_sheets.py
```

### `check_auth_status.py`
Check the authentication status of Gmail and Google Sheets APIs.

```bash
python scripts/check_auth_status.py
```

## Setup Scripts

### `setup_bulk_email.py`
Initialize the bulk email system with required configurations.

```bash
python scripts/setup_bulk_email.py
```

### `initialize_email_tracking.py`
Set up Google Sheets tracking tab with proper headers and formatting.

```bash
python scripts/initialize_email_tracking.py
```

## Utility Scripts

### `list_sheets.py`
List all sheets in the configured Google Spreadsheet.

```bash
python scripts/list_sheets.py
```

### `view_tracking_data.py`
View current email tracking data from Google Sheets.

```bash
python scripts/view_tracking_data.py
```

## Example Scripts

### `example_bulk_email_usage.py`
Example code demonstrating how to use the bulk email system.

```bash
python scripts/example_bulk_email_usage.py
```

## Prerequisites

All scripts require:
- Python 3.10+
- Configured `.env` file with API credentials
- Gmail and Sheets OAuth2 credentials in `credentials/` directory

## First-Time Setup

1. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

2. Authenticate APIs:
```bash
./scripts/authenticate_apis.sh
```

3. Initialize tracking:
```bash
python scripts/initialize_email_tracking.py
```

4. Verify setup:
```bash
python scripts/check_auth_status.py
```

## Troubleshooting

### "Credentials not found"
- Ensure `credentials/gmail_credentials.json` and `credentials/sheets_credentials.json` exist
- Download from Google Cloud Console if missing

### "Authentication failed"
- Check that redirect URIs are configured in Google Cloud Console
- Verify API_BASE_URL in `.env` matches your server URL

### "Permission denied"
- Run `chmod +x scripts/*.sh` to make bash scripts executable
