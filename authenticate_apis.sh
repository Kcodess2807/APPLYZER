#!/bin/bash

# Quick script to authenticate Gmail and Google Sheets

echo "==================================="
echo "API Authentication Helper"
echo "==================================="
echo ""

BASE_URL="http://localhost:8000/api/v1"

# Check if server is running
echo "Checking if server is running..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo "Please start the server first: make run"
    exit 1
fi
echo "✅ Server is running"
echo ""

# Gmail Authentication
echo "==================================="
echo "1. Gmail Authentication"
echo "==================================="
echo ""

GMAIL_STATUS=$(curl -s "$BASE_URL/gmail/status" | grep -o '"authenticated":[^,}]*' | cut -d':' -f2)

if [ "$GMAIL_STATUS" = "true" ]; then
    echo "✅ Gmail is already authenticated"
else
    echo "Gmail is not authenticated. Starting OAuth flow..."
    AUTH_URL=$(curl -s "$BASE_URL/gmail/authenticate" | grep -o '"authorization_url":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$AUTH_URL" ]; then
        echo ""
        echo "Please visit this URL to authorize Gmail:"
        echo ""
        echo "$AUTH_URL"
        echo ""
        echo "After authorizing, press Enter to continue..."
        read
        
        # Check status again
        GMAIL_STATUS=$(curl -s "$BASE_URL/gmail/status" | grep -o '"authenticated":[^,}]*' | cut -d':' -f2)
        if [ "$GMAIL_STATUS" = "true" ]; then
            echo "✅ Gmail authenticated successfully!"
        else
            echo "⚠️  Gmail authentication may have failed. Check manually."
        fi
    else
        echo "❌ Failed to get authorization URL"
        echo "Make sure credentials/gmail_credentials.json exists"
    fi
fi

echo ""

# Google Sheets Authentication
echo "==================================="
echo "2. Google Sheets Authentication"
echo "==================================="
echo ""

SHEETS_STATUS=$(curl -s "$BASE_URL/sheets/status" | grep -o '"authenticated":[^,}]*' | cut -d':' -f2)

if [ "$SHEETS_STATUS" = "true" ]; then
    echo "✅ Google Sheets is already authenticated"
else
    echo "Google Sheets is not authenticated. Starting OAuth flow..."
    AUTH_URL=$(curl -s "$BASE_URL/sheets/authenticate" | grep -o '"authorization_url":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$AUTH_URL" ]; then
        echo ""
        echo "Please visit this URL to authorize Google Sheets:"
        echo ""
        echo "$AUTH_URL"
        echo ""
        echo "After authorizing, press Enter to continue..."
        read
        
        # Check status again
        SHEETS_STATUS=$(curl -s "$BASE_URL/sheets/status" | grep -o '"authenticated":[^,}]*' | cut -d':' -f2)
        if [ "$SHEETS_STATUS" = "true" ]; then
            echo "✅ Google Sheets authenticated successfully!"
        else
            echo "⚠️  Sheets authentication may have failed. Check manually."
        fi
    else
        echo "❌ Failed to get authorization URL"
        echo "Make sure credentials/sheets_credentials.json exists"
    fi
fi

echo ""
echo "==================================="
echo "Authentication Complete!"
echo "==================================="
echo ""
echo "Status:"
curl -s "$BASE_URL/gmail/status" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  Gmail: /'
curl -s "$BASE_URL/sheets/status" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  Sheets: /'
echo ""
echo "Note: Google Sheets is optional. You can still send emails without it."
echo ""
