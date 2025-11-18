#!/usr/bin/env python3
"""
Create Supabase storage bucket for video transcripts
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def create_bucket():
    """Create the video-transcripts bucket in Supabase"""
    supabase_url = os.getenv("SUPABASE_URL", "https://jlfqzcaospvspmzbvbxd.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_key:
        print("Error: SUPABASE_KEY must be set in environment or .env file")
        sys.exit(1)
    
    client: Client = create_client(supabase_url, supabase_key)
    bucket_name = "video-transcripts"
    
    print(f"Creating bucket: {bucket_name}")
    print(f"Supabase URL: {supabase_url}\n")
    
    try:
        # Check if bucket exists
        buckets = client.storage.list_buckets()
        existing_buckets = [b.name for b in buckets]
        
        if bucket_name in existing_buckets:
            print(f"✅ Bucket '{bucket_name}' already exists!")
            return True
        
        # Try to create bucket using storage API
        # Note: This requires service role key for bucket creation
        # For free tier, bucket creation might need to be done via dashboard
        
        # Try using the storage API
        try:
            # The Supabase Python client doesn't have a direct create_bucket method
            # We need to use the REST API directly or create via dashboard
            print("⚠️  Bucket creation via API requires service role key.")
            print("   For free tier, please create the bucket manually:")
            print(f"   1. Go to Supabase Dashboard → Storage")
            print(f"   2. Click 'Create Bucket'")
            print(f"   3. Name: {bucket_name}")
            print(f"   4. Public: Yes (required for free tier)")
            print(f"   5. Click 'Create'")
            return False
        except Exception as e:
            print(f"Error: {e}")
            print("\nPlease create the bucket manually in Supabase Dashboard")
            return False
            
    except Exception as e:
        print(f"Error checking/creating bucket: {e}")
        print("\nPlease create the bucket manually:")
        print(f"  1. Go to Supabase Dashboard → Storage")
        print(f"  2. Create bucket: {bucket_name}")
        print(f"  3. Set it to Public")
        return False

if __name__ == "__main__":
    success = create_bucket()
    sys.exit(0 if success else 1)

