#!/usr/bin/env python3
"""
Sync car_listings to market_prices
Keeps market intelligence data fresh
"""

from database.connection import get_session
from database.models import MarketPrice
from sqlalchemy import text
import sys

def sync_listings_to_market():
    """Copy car_listings to market_prices"""
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🔄 SYNCING car_listings → market_prices                         ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        with get_session() as session:
            # Check current counts
            result = session.execute(text("SELECT COUNT(*) FROM car_listings")).scalar()
            car_listings_count = result or 0
            
            result = session.execute(text("SELECT COUNT(*) FROM market_prices")).scalar()
            market_prices_count = result or 0
            
            print(f"📊 Current Status:")
            print(f"   car_listings: {car_listings_count} records")
            print(f"   market_prices: {market_prices_count} records")
            print()
            
            if car_listings_count == 0:
                print("❌ No data in car_listings table!")
                return False
            
            # Sync data
            print("🔄 Syncing data...")
            
            sync_query = text("""
                INSERT INTO market_prices (
                    brand, model, year, kilometers, fuel, 
                    transmission, city, price, source, last_seen
                )
                SELECT 
                    brand, model, year, kilometers, fuel,
                    transmission, city, price, source, created_at
                FROM car_listings
                ON CONFLICT (brand, model, year, city, source) 
                DO UPDATE SET
                    price = EXCLUDED.price,
                    kilometers = EXCLUDED.kilometers,
                    last_seen = EXCLUDED.last_seen
            """)
            
            session.execute(sync_query)
            session.commit()
            
            # Check new count
            result = session.execute(text("SELECT COUNT(*) FROM market_prices")).scalar()
            new_count = result or 0
            
            print()
            print("✅ Sync Complete!")
            print(f"   market_prices now has: {new_count} records")
            print(f"   Added/Updated: {new_count - market_prices_count} records")
            print()
            print("🎉 Market intelligence is now ready to use!")
            
            return True
            
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return False

if __name__ == "__main__":
    success = sync_listings_to_market()
    sys.exit(0 if success else 1)
