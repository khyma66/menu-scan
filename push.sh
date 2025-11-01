#!/bin/bash

# Quick script to push menu-ocr to GitHub
# Make sure you've created the repository on GitHub first!

echo "🚀 Pushing Menu OCR to GitHub..."
echo ""

# Check if remote already exists
if git remote | grep -q origin; then
    echo "⚠️  Remote 'origin' already exists!"
    echo "Current remote:"
    git remote -v
    echo ""
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin https://github.com/mohan6695/menu-ocr.git
    else
        echo "Skipping remote setup..."
    fi
else
    echo "Adding remote repository..."
    git remote add origin https://github.com/mohan6695/menu-ocr.git
fi

echo ""
echo "📦 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 View your repo: https://github.com/mohan6695/menu-ocr"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Possible reasons:"
    echo "  • Repository doesn't exist yet on GitHub"
    echo "  • Authentication issue"
    echo "  • Network problem"
    echo ""
    echo "Fix:"
    echo "  1. Create repo at https://github.com/new"
    echo "  2. Run this script again"
fi

