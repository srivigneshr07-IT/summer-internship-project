#!/usr/bin/env python3
"""
Auto-sync wrapper for scraper
Runs scraper then syncs to market_prices
"""

import subprocess
import sys

def run_scraper_with_sync():
    """Run scraper and auto-sync to market_prices"""
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🚀 SCRAPER WITH AUTO-SYNC                                       ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Step 1: Run scraper
    print("📡 Step 1: Running scraper...")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            ["python", "scrape_luxury_cars_auto.py"],
            check=True,
            capture_output=False
        )
        print()
        print("✅ Scraping complete!")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Scraping failed: {e}")
        return False
    
    # Step 2: Sync to market_prices
    print("🔄 Step 2: Syncing to market_prices...")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            ["python", "sync_market_data.py"],
            check=True,
            capture_output=False
        )
        print()
        print("✅ Sync complete!")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Sync failed: {e}")
        return False
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     ✅ SCRAPER + SYNC COMPLETE                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🎉 New data is now available for:")
    print("   ✅ Market intelligence (predictions)")
    print("   ✅ Model retraining (future)")
    
    return True

if __name__ == "__main__":
    success = run_scraper_with_sync()
    sys.exit(0 if success else 1)
