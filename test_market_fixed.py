#!/usr/bin/env python3
"""Test market intelligence with correct column"""

from database.connection import get_session
from database.models import MarketPrice
from datetime import datetime, timedelta

print("Testing market intelligence query (fixed)...")
print("="*60)

try:
    with get_session() as session:
        # Test query for Maruti Swift
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        print(f"Cutoff date: {cutoff_date}")
        print()
        
        # Query with correct column name
        query = session.query(MarketPrice).filter(
            MarketPrice.brand.ilike('%maruti%'),
            MarketPrice.model.ilike('%swift%'),
            MarketPrice.last_seen_at >= cutoff_date
        )
        
        count = query.count()
        
        print(f"Query: Maruti Swift (last 30 days)")
        print(f"Found: {count} records")
        print()
        
        if count > 0:
            print("✅ Market intelligence WILL WORK!")
            print()
            print("Sample records:")
            for record in query.limit(5):
                print(f"  - {record.brand} {record.model} ({record.year}): ₹{record.price:,.0f}")
                print(f"    Last seen: {record.last_seen_at}")
        else:
            print("❌ Still no records found!")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*60)
