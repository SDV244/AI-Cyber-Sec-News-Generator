#!/bin/bash
# Cybersecurity Newsletter Automation — Setup Script

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright Chromium..."
playwright install chromium

echo "Installing WeasyPrint system dependencies..."
# Debian/Ubuntu:
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1

echo "Creating output directories..."
mkdir -p output logs

echo "Setting up .env file..."
cp .env.example .env
echo "⚠️  Edit .env with your API keys before running!"

echo "✅ Setup complete. Run: python cyber_newsletter.py --run-now"
