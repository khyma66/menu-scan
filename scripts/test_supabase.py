#!/usr/bin/env python3
"""Test Supabase connectivity."""

import os
import sys
sys.path.append('fastapi-menu-service')

from supabase import create_client

def test_supabase():
    """Test Supabase connection."""
    supabase_url = "https://jlfqzcaospvspmzbvbxd.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsZnF6Y2Fvc3B2c3BtemJ2YnhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTM3MDMzNiwiZXhwIjoyMDc2OTQ2MzM2fQ.5xdkvyJSsza79Iz3kiASMEE22WhNbBktQD6QBb2UgBY"

    try:
        client = create_client(supabase_url, supabase_key)
        # Try to fetch from a table, say ocr_results
        response = client.table("ocr_results").select("*").limit(1).execute()
        print("Supabase connection successful!")
        print(f"Found {len(response.data)} records in ocr_results table.")
        return True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase()