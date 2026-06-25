"""
Market Intelligence Engine
Provides real-time market insights for car pricing
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy import func
from database.connection import get_session
from database.models import MarketPrice


class MarketIntelligence:
    """Query market data and provide pricing insights"""
    
    def __init__(self, freshness_days: int = 30):
        """
        Initialize Market Intelligence Engine
        
        Args:
            freshness_days: Only use listings seen in last N days (default: 30)
        """
        self.freshness_days = freshness_days
    
    def get_market_insights(
        self,
        brand: str,
        model: str,
        year: int,
        city: str,
        fuel: Optional[str] = None,
        transmission: Optional[str] = None
    ) -> Dict:
        """
        Get market insights for a specific car
        
        Args:
            brand: Car brand (e.g., "Maruti")
            model: Car model (e.g., "Swift")
            year: Manufacturing year
            city: City name
            fuel: Fuel type (optional)
            transmission: Transmission type (optional)
        
        Returns:
            Dictionary with market insights
        """
        with get_session() as session:
            # Calculate freshness cutoff
            cutoff_date = datetime.utcnow() - timedelta(days=self.freshness_days)
            
            # Normalize brand name (remove extra words)
            brand_normalized = brand.lower().split()[0] if brand else ""
            
            # Base query - filter by brand, model, city, and freshness
            # Use ILIKE for case-insensitive partial matching
            query = session.query(MarketPrice).filter(
                MarketPrice.brand.ilike(f'%{brand_normalized}%'),
                MarketPrice.model.ilike(f'%{model}%'),
                MarketPrice.city.ilike(f'%{city}%'),
                MarketPrice.last_seen_at >= cutoff_date
            )
            
            # Add optional filters
            if fuel:
                query = query.filter(MarketPrice.fuel.ilike(f'%{fuel}%'))
            if transmission:
                query = query.filter(MarketPrice.transmission.ilike(f'%{transmission}%'))
            
            # Get all matching listings
            listings = query.all()
            
            if not listings:
                return self._no_data_response()
            
            # Calculate statistics
            prices = [listing.price for listing in listings]
            sample_size = len(prices)
            
            # Basic stats
            avg_price = sum(prices) / sample_size
            median_price = sorted(prices)[sample_size // 2]
            min_price = min(prices)
            max_price = max(prices)
            
            # Confidence level based on sample size
            confidence = self._calculate_confidence(sample_size)
            
            # Year-specific insights (cars within ±2 years)
            year_specific = [l for l in listings if abs(l.year - year) <= 2]
            year_specific_prices = [l.price for l in year_specific] if year_specific else []
            
            return {
                "status": "success",
                "market_data_available": True,
                "sample_size": sample_size,
                "confidence": confidence,
                "statistics": {
                    "average_price": round(avg_price),
                    "median_price": round(median_price),
                    "min_price": min_price,
                    "max_price": max_price,
                    "price_range": max_price - min_price
                },
                "year_specific": {
                    "sample_size": len(year_specific_prices),
                    "average_price": round(sum(year_specific_prices) / len(year_specific_prices)) if year_specific_prices else None,
                    "median_price": sorted(year_specific_prices)[len(year_specific_prices) // 2] if year_specific_prices else None
                },
                "filters_applied": {
                    "brand": brand,
                    "model": model,
                    "year": year,
                    "city": city,
                    "fuel": fuel,
                    "transmission": transmission,
                    "freshness_days": self.freshness_days
                },
                "sample_listings": [
                    {
                        "price": l.price,
                        "year": l.year,
                        "kilometers": l.kilometers,
                        "source": l.source,
                        "last_seen": str(l.last_seen_at)
                    }
                    for l in listings[:5]  # Show top 5 samples
                ]
            }
    
    def get_city_market_overview(self, city: str) -> Dict:
        """Get overall market overview for a city"""
        with get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=self.freshness_days)
            
            # Get all fresh listings in city
            listings = session.query(MarketPrice).filter(
                MarketPrice.city == city,
                MarketPrice.last_seen_at >= cutoff_date
            ).all()
            
            if not listings:
                return {"status": "no_data", "city": city}
            
            prices = [l.price for l in listings]
            
            # Brand distribution
            brand_counts = {}
            for listing in listings:
                brand_counts[listing.brand] = brand_counts.get(listing.brand, 0) + 1
            
            return {
                "status": "success",
                "city": city,
                "total_listings": len(listings),
                "average_price": round(sum(prices) / len(prices)),
                "median_price": sorted(prices)[len(prices) // 2],
                "price_range": {
                    "min": min(prices),
                    "max": max(prices)
                },
                "top_brands": sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
    
    def get_brand_insights(self, brand: str, city: Optional[str] = None) -> Dict:
        """Get market insights for a specific brand"""
        with get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=self.freshness_days)
            
            query = session.query(MarketPrice).filter(
                MarketPrice.brand == brand,
                MarketPrice.last_seen_at >= cutoff_date
            )
            
            if city:
                query = query.filter(MarketPrice.city == city)
            
            listings = query.all()
            
            if not listings:
                return {"status": "no_data", "brand": brand}
            
            prices = [l.price for l in listings]
            
            # Model distribution
            model_counts = {}
            for listing in listings:
                model_counts[listing.model] = model_counts.get(listing.model, 0) + 1
            
            return {
                "status": "success",
                "brand": brand,
                "city": city,
                "total_listings": len(listings),
                "average_price": round(sum(prices) / len(prices)),
                "median_price": sorted(prices)[len(prices) // 2],
                "top_models": sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size"""
        if sample_size >= 10:
            return "high"
        elif sample_size >= 5:
            return "medium"
        elif sample_size >= 2:
            return "low"
        else:
            return "very_low"
    
    def _no_data_response(self) -> Dict:
        """Return response when no market data is available"""
        return {
            "status": "no_data",
            "market_data_available": False,
            "sample_size": 0,
            "confidence": "none",
            "message": "No market data available for this car. Using ML prediction only."
        }
