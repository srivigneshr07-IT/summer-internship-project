#!/usr/bin/env python3
"""Test predict endpoint"""

import requests
import json

# Test payload
payload = {
    "brand": "Maruti",
    "model": "Swift",
    "fuel_type": "Petrol",
    "transmission": "Manual",
    "kilometers": 45000,
    "owner_type": "First",
    "city": "Chennai",
    "car_age": 8,
    "premium_brand": 0,
    "transaction_type": "selling"
}

print("Testing /predict endpoint...")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(
        "http://localhost:8000/predict",
        json=payload,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
