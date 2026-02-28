#!/usr/bin/env python3
"""
Test script to check the menu table structure and contents.
"""

import os
import sys
sys.path.append('fastapi-menu-service')

# Load environment variables from .env.secrets
from dotenv import load_dotenv
load_dotenv('fastapi-menu-service/.env.secrets')

from app.services.supabase_client import SupabaseClient

def main():
    # Initialize Supabase client
    supabase = SupabaseClient()

    if not supabase.client:
        print("❌ Failed to initialize Supabase client")
        return

    try:
        # Try to get a sample record
        print("🔍 Checking menu table...")
        response = supabase.client.table("menu").select("*").limit(1).execute()

        if response.data and len(response.data) > 0:
            sample = response.data[0]
            print(f"✅ Menu table exists with columns: {list(sample.keys())}")
            print(f"Sample record: {sample}")

            # Get total count
            count_response = supabase.client.table("menu").select("*", count="exact").limit(1).execute()
            total_count = count_response.count if hasattr(count_response, 'count') else "unknown"
            print(f"Total records in menu table: {total_count}")

            # Get enrichment status counts
            pending_count = supabase.client.table("menu").select("*", count="exact").eq("enrichment_status", "pending").limit(1).execute()
            completed_count = supabase.client.table("menu").select("*", count="exact").eq("enrichment_status", "completed").limit(1).execute()
            failed_count = supabase.client.table("menu").select("*", count="exact").eq("enrichment_status", "failed").limit(1).execute()

            print(f"Pending: {pending_count.count if hasattr(pending_count, 'count') else 'unknown'}")
            print(f"Completed: {completed_count.count if hasattr(completed_count, 'count') else 'unknown'}")
            print(f"Failed: {failed_count.count if hasattr(failed_count, 'count') else 'unknown'}")

        else:
            print("❌ Menu table is empty or doesn't exist")

    except Exception as e:
        print(f"❌ Error querying menu table: {e}")

if __name__ == "__main__":
    main()