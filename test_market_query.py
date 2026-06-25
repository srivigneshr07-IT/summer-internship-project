#!/usr/bin/env python3
"""Test market intelligence query"""

from database.connection import get_session
from database.models import MarketPrice
from datetime import datetime, timedelta

print("Testing market intelligence query...")
print("="*60)

try:
    with get_session() as session:
        # Test query for Maruti Swift
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        query = session.query(MarketPrice).filter(
            MarketPrice.brand.ilike('%maruti%'),
            MarketPrice.model.ilike('%swift%'),
            MarketPrice.last_seen >= cutoff_date
        )
        
        count = query.count()
        
        print(f"Query: Maruti Swift (last 30 days)")
        print(f"Found: {count} records")
        print()
        
        if count > 0:
            print("Sample records:")
            for record in query.limit(5):
                print(f"  - {record.brand} {record.model} ({record.year}): ₹{record.price:,.0f}")
                print(f"    Last seen: {record.last_seen}")
        else:
            print("❌ No records found!")
            print()
            print("Checking why:")
            
            # Check total Maruti Swift (any date)
            total = session.query(MarketPrice).filter(
                MarketPrice.brand.ilike('%maruti%'),
                MarketPrice.model.ilike('%swift%')
            ).count()
            print(f"  Total Maruti Swift (all dates): {total}")
            
            # Check last_seen dates
            sample = session.query(MarketPrice).filter(
                MarketPrice.brand.ilike('%maruti%'),
                MarketPrice.model.ilike('%swift%')
            ).first()
            
            if sample:
                print(f"  Sample last_seen: {sample.last_seen}")
                print(f"  Cutoff date: {cutoff_date}")
                print(f"  Issue: last_seen is older than 30 days!")
                
except Exception as e:
    print(f"❌ Error: {e}")

print("="*60)
