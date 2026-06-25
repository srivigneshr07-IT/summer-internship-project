#!/usr/bin/env python3
"""Debug market intelligence"""

import sys
sys.path.insert(0, '/workspaces/internship-project-final')

from pricing import DynamicPricingEngine

# Test market intelligence
engine = DynamicPricingEngine()

print("Testing market intelligence...")
print("="*60)

result = engine.get_dynamic_price(
    ml_prediction=500000,
    brand="Maruti",
    model="Swift",
    year=2018,
    city="Chennai",
    fuel="Petrol",
    transmission="Manual"
)

print(f"Status: {result['status']}")
print(f"Final Price: ₹{result['final_price']:,.0f}")
print(f"Market Context: {result.get('market_context', {})}")
print(f"Pricing Breakdown: {result.get('pricing_breakdown', {})}")
print("="*60)

if result['status'] == 'success':
    print("✅ Market intelligence is working!")
else:
    print("❌ Market intelligence failed!")
    print(f"Error: {result.get('error', 'Unknown')}")
