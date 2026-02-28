#!/usr/bin/env python3
"""
Check what a completed enrichment record looks like.
"""

import os
import sys
sys.path.append('fastapi-menu-service')

from dotenv import load_dotenv
load_dotenv('fastapi-menu-service/.env.secrets')

from app.services.supabase_client import SupabaseClient

def main():
    supabase = SupabaseClient()

    if not supabase.client:
        print("❌ Failed to initialize Supabase client")
        return

    try:
        # Get a completed record
        response = supabase.client.table("menu").select("*").eq("enrichment_status", "completed").limit(1).execute()

        if response.data and len(response.data) > 0:
            record = response.data[0]
            print("✅ Sample completed record:")
            for key, value in record.items():
                if value is not None and value != "" and value != False:
                    print(f"  {key}: {value}")
        else:
            print("❌ No completed records found")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()