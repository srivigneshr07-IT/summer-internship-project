#!/usr/bin/env python3
"""Count total variants in database"""

from database.connection import get_session
from sqlalchemy import text

print("Checking variants in database...")
print("="*60)

try:
    with get_session() as session:
        # Count total unique variants
        result = session.execute(text("""
            SELECT COUNT(DISTINCT variant) as variant_count
            FROM market_prices
            WHERE variant IS NOT NULL AND variant != ''
        """))
        
        total_variants = result.scalar()
        
        print(f"Total unique variants: {total_variants}")
        print()
        
        # Count by brand
        result = session.execute(text("""
            SELECT brand, COUNT(DISTINCT variant) as variant_count
            FROM market_prices
            WHERE variant IS NOT NULL AND variant != ''
            GROUP BY brand
            ORDER BY variant_count DESC
            LIMIT 10
        """))
        
        print("Top 10 brands by variant count:")
        for row in result:
            print(f"  {row[0]}: {row[1]} variants")
        
        print()
        
        # Show some sample variants
        result = session.execute(text("""
            SELECT brand, model, variant
            FROM market_prices
            WHERE variant IS NOT NULL AND variant != ''
            LIMIT 10
        """))
        
        print("Sample variants:")
        for row in result:
            print(f"  {row[0]} {row[1]} - {row[2]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("="*60)
