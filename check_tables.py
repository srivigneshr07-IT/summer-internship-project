#!/usr/bin/env python3
"""Check what tables exist in database"""

from database.connection import get_session
from sqlalchemy import text

print("Checking database tables...")
print("="*60)

try:
    with get_session() as session:
        # List all tables
        result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            # Count records in each table
            try:
                count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"  ✅ {table}: {count} records")
            except Exception as e:
                print(f"  ⚠️  {table}: Error - {e}")
        
        print()
        print("="*60)
        
        if 'car_listings' not in tables:
            print("❌ car_listings table does NOT exist!")
            print()
            print("Your data is probably in one of these tables:")
            for table in tables:
                if 'listing' in table.lower() or 'price' in table.lower() or 'car' in table.lower():
                    print(f"   → {table}")
        
except Exception as e:
    print(f"❌ Database error: {e}")
