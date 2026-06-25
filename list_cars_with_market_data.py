#!/usr/bin/env python3
"""List all cars with market data (brand, model, variants)"""

from database.connection import get_session
from sqlalchemy import text

print("Cars with market data in database:")
print("="*80)

try:
    with get_session() as session:
        # Get all brands with their models and variants
        result = session.execute(text("""
            SELECT 
                brand,
                model,
                COUNT(DISTINCT variant) as variant_count,
                COUNT(*) as listing_count,
                STRING_AGG(DISTINCT variant, ', ' ORDER BY variant) as variants
            FROM market_prices
            WHERE brand IS NOT NULL 
              AND model IS NOT NULL
            GROUP BY brand, model
            ORDER BY brand, model
        """))
        
        current_brand = None
        total_models = 0
        
        for row in result:
            brand, model, variant_count, listing_count, variants = row
            
            # Print brand header
            if brand != current_brand:
                if current_brand is not None:
                    print()
                print(f"\n{brand.upper()}")
                print("-" * 80)
                current_brand = brand
            
            # Print model and variants
            print(f"  {model} ({listing_count} listings, {variant_count} variants)")
            if variants:
                # Truncate if too long
                variant_list = variants if len(variants) < 100 else variants[:97] + "..."
                print(f"    Variants: {variant_list}")
            
            total_models += 1
        
        print()
        print("="*80)
        print(f"Total: {total_models} models across all brands")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
