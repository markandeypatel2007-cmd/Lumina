"""
Standalone diagnostic: calls the OpenWeb Ninja product-details endpoint
directly and prints exactly what comes back, so we can see the real
response shape/error instead of the silent None from url_analyzer.py.

Run:
    python test_api.py
"""

import os
import requests
from url_analyzer import _get_api_key, OPENWEBNINJA_BASE_URL

OPENWEBNINJA_API_KEY = _get_api_key()

# Use one of the curated benchmark ASINs so we know the product definitely exists.
TEST_ASIN = "B09XS7JWHH"  # Sony WH-1000XM5

print(f"Key loaded: {'YES' if OPENWEBNINJA_API_KEY else 'NO — empty string'}")
print(f"Key starts with: {OPENWEBNINJA_API_KEY[:6]}..." if OPENWEBNINJA_API_KEY else "")

headers = {"x-api-key": OPENWEBNINJA_API_KEY}

resp = requests.get(
    f"{OPENWEBNINJA_BASE_URL}/product-details",
    headers=headers,
    params={"asin": TEST_ASIN, "country": "US"},
    timeout=15,
)

print(f"\nStatus code: {resp.status_code}")
print(f"Response body (first 2000 chars):\n{resp.text[:2000]}")