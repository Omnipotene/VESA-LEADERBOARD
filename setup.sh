#!/bin/bash
# VESA Scraper Setup Script

echo "=========================================="
echo "VESA League Scraper - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo ".env file created"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/urls_template.csv with your Overstat.gg URLs"
echo "2. Save it as config/urls.csv"
echo "3. Run: python3 main.py --urls config/urls.csv"
echo ""
echo "For help: python3 main.py --help"
echo ""
