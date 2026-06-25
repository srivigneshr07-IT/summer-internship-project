#!/usr/bin/env python3
"""Check and populate market_prices table"""

import sys
sys.path.insert(0, '/workspaces/internship-project-final')

from database.connection import get_session
from database.models import MarketPrice
from datetime import datetime

print("Checking market_prices table...")
print("="*60)

try:
    with get_session() as session:
        # Count total records
        count = session.query(MarketPrice).count()
        print(f"Total records in market_prices: {count}")
        
        if count == 0:
            print("\n❌ NO DATA IN market_prices TABLE!")
            print("\nThis is why market intelligence shows '--'")
            print("\nYou need to:")
            print("1. Run the scraper to collect data")
            print("2. Or import existing data from car_listings table")
            
        else:
            print(f"\n✅ Found {count} records")
            
            # Show sample
            sample = session.query(MarketPrice).limit(5).all()
            print("\nSample records:")
            for record in sample:
                print(f"  - {record.brand} {record.model} ({record.year}): ₹{record.price:,.0f}")
                
except Exception as e:
    print(f"\n❌ Database error: {e}")
    print("\nCheck your .env file:")
    print("  - POSTGRES_HOST")
    print("  - POSTGRES_USER")
    print("  - POSTGRES_PASSWORD")

print("="*60)
