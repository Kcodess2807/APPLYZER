#!/bin/bash

# Cleanup script for GitHub push
# Removes redundant documentation and temporary files

echo "🧹 Cleaning up repository for GitHub..."
echo ""

# Remove redundant documentation files
echo "Removing redundant documentation..."
rm -f AUTHENTICATION_COMPLETE_GUIDE.md
rm -f BULK_EMAIL_GUIDE.md
rm -f BULK_EMAIL_QUICKSTART.md
rm -f BULK_EMAIL_README.md
rm -f FIX_SHEETS_AUTH.md
rm -f GETTING_STARTED_CHECKLIST.md
rm -f IMPLEMENTATION_SUMMARY.md
rm -f SHEETS_AUTHENTICATION_FIX.md
rm -f SIMPLE_FIX.md
rm -f START_HERE.md
rm -f SYSTEM_ARCHITECTURE.md
rm -f TROUBLESHOOTING.md

# Remove temporary/helper scripts
echo "Removing temporary scripts..."
rm -f check_auth_status.py
rm -f example_bulk_email_usage.py
rm -f list_sheets.py
rm -f setup_bulk_email.py
rm -f test_api_endpoints.py
rm -f test_bulk_email_system.py
rm -f view_tracking_data.py

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Files kept:"
echo "  ✓ Core application code (app/)"
echo "  ✓ initialize_email_tracking.py"
echo "  ✓ authenticate_sheets.py"
echo "  ✓ README.md"
echo "  ✓ GOOGLE_APPS_SCRIPT_AUTOMATION.md"
echo "  ✓ API_ENDPOINTS.md"
echo "  ✓ GMAIL_SETUP_GUIDE.md"
echo "  ✓ PROJECT_STRUCTURE.md"
echo "  ✓ QUICK_START.md"
echo ""
echo "Next steps:"
echo "  1. Review the updated README.md"
echo "  2. Add .env to .gitignore (if not already)"
echo "  3. Add credentials/ to .gitignore"
echo "  4. Run: git add ."
echo "  5. Run: git commit -m 'Add bulk email system'"
echo "  6. Run: git push"
