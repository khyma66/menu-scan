#!/bin/bash

# Render deployment helper script

echo "🚀 Deploying Menu OCR API to Render..."
echo ""
echo "Make sure you have:"
echo "1. Connected your GitHub repository to Render"
echo "2. Set up environment variables in Render dashboard"
echo "3. Configured Redis addon"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo "✅ Ready to deploy!"
echo "Go to https://dashboard.render.com and deploy from your repository."
echo ""
echo "Environment variables to set in Render:"
echo "- SUPABASE_URL"
echo "- SUPABASE_KEY"
echo "- SUPABASE_BUCKET"
echo "- OPENAI_API_KEY (optional)"
echo "- ANTHROPIC_API_KEY (optional)"
echo "- LLM_MODEL"
echo "- FALLBACK_ENABLED"

