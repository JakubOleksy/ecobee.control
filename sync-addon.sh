#!/bin/bash

# Sync source files to Home Assistant addon directory
# Run this script whenever you make changes to the source code

set -e

echo "Syncing files to addon directory..."

# Copy source code
cp -r src addon/
echo "✓ Copied src/"

# Copy Python files
cp cli.py addon/
echo "✓ Copied cli.py"

cp api_server.py addon/
echo "✓ Copied api_server.py"

# Copy dependencies
cp requirements.txt addon/
echo "✓ Copied requirements.txt"

# Copy default config
cp config/default.yml addon/
echo "✓ Copied config/default.yml"

echo ""
echo "✅ Addon files synced successfully!"
echo ""
echo "Next steps:"
echo "1. Go to Home Assistant → Settings → Add-ons"
echo "2. Click 'Rebuild' on the Ecobee Web Control add-on"
echo "3. Restart the add-on after rebuild completes"
