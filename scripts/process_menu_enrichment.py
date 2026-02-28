#!/usr/bin/env python3
"""
Script to process menu enrichment in batches.
"""

import subprocess
import time
import json

def run_batch(offset, batch_size=20):
    """Run a single batch of enrichment."""
    cmd = f'curl -s -X POST "http://localhost:8000/menu-enrichment/enrich-batch?limit={batch_size}&offset={offset}&status_filter=pending"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            if data.get("success"):
                processed = data["result"]["processed"]
                success = data["result"]["success"]
                failed = data["result"]["failed"]
                return processed, success, failed
        except json.JSONDecodeError:
            pass

    print(f"Error running batch at offset {offset}: {result.stderr}")
    return 0, 0, 0

def main():
    batch_size = 20
    total_processed = 0
    total_success = 0
    total_failed = 0
    batch_num = 0

    print("🚀 Starting menu enrichment processing...")
    print(f"Batch size: {batch_size}")
    print("=" * 60)

    while True:
        batch_num += 1
        print(f"📦 Processing batch #{batch_num}...")

        processed, success, failed = run_batch(0, batch_size)  # Always start from offset 0 since we filter by status

        if processed == 0:
            print("✅ No more dishes to process!")
            break

        total_processed += processed
        total_success += success
        total_failed += failed

        print(f"   ✅ Success: {success} | ❌ Failed: {failed}")
        print(f"   📊 Cumulative: {total_processed} processed | {total_success} success | {total_failed} failed")
        print("-" * 60)

        # Brief pause between batches
        time.sleep(2)

    print("=" * 60)
    print("🎉 Enrichment completed!")
    print(f"📊 Final Statistics:")
    print(f"   Total processed: {total_processed}")
    print(f"   Successful: {total_success}")
    print(f"   Failed: {total_failed}")

if __name__ == "__main__":
    main()