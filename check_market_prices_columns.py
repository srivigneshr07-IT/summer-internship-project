#!/usr/bin/env python3
"""Check market_prices table structure"""

from database.connection import get_session
from sqlalchemy import text

print("Checking market_prices table structure...")
print("="*60)

try:
    with get_session() as session:
        # Get column names
        result = session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'market_prices'
            ORDER BY ordinal_position
        """))
        
        print("Columns in market_prices:")
        for row in result:
            print(f"  - {row[0]} ({row[1]})")
        
        print()
        print("="*60)
        
        # Show sample record
        result = session.execute(text("SELECT * FROM market_prices LIMIT 1"))
        row = result.fetchone()
        
        if row:
            print("\nSample record:")
            for i, col in enumerate(result.keys()):
                print(f"  {col}: {row[i]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
