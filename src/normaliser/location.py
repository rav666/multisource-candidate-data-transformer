"""
location.py — Parse a raw location string into a structured Location object.

Strategy:
  1. Split by comma into parts (city, region, country).
  2. Try to resolve each part against known country aliases -> ISO-3166 alpha-2.
  3. For single-part strings, look up known city -> country table.
"""
from __future__ import annotations

from src.models import Location

# ISO-3166 country lookup (name / alias -> alpha-2)
COUNTRY_MAP: dict[str, str] = {
    "india": "IN", "bharat": "IN",
    "united states": "US", "usa": "US", "u.s.a.": "US", "u.s.": "US",
    "united kingdom": "GB", "uk": "GB", "great britain": "GB",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "singapore": "SG",
    "netherlands": "NL",
    "japan": "JP",
    "china": "CN",
    "brazil": "BR",
    "south africa": "ZA",
    "uae": "AE", "united arab emirates": "AE",
    "ireland": "IE",
    "new zealand": "NZ",
    "sweden": "SE",
    "switzerland": "CH",
    "poland": "PL",
    "spain": "ES",
    "italy": "IT",
    "portugal": "PT",
    "israel": "IL",
    "south korea": "KR", "korea": "KR",
    "russia": "RU",
}

# Known cities -> ISO-3166 country code
CITY_COUNTRY: dict[str, str] = {
    # India
    "bengaluru": "IN", "bangalore": "IN",
    "mumbai": "IN", "bombay": "IN",
    "delhi": "IN", "new delhi": "IN",
    "hyderabad": "IN",
    "chennai": "IN", "madras": "IN",
    "pune": "IN",
    "kolkata": "IN", "calcutta": "IN",
    "noida": "IN",
    "gurgaon": "IN", "gurugram": "IN",
    "ahmedabad": "IN",
    "jaipur": "IN",
    "surat": "IN",
    "lucknow": "IN",
    "kochi": "IN",
    "chandigarh": "IN",
    "mysuru": "IN", "mysore": "IN",
    "coimbatore": "IN",
    "manipal": "IN",
    # USA
    "new york": "US", "nyc": "US",
    "san francisco": "US", "sf": "US",
    "seattle": "US",
    "boston": "US",
    "chicago": "US",
    "austin": "US",
    "los angeles": "US", "la": "US",
    "san jose": "US",
    "denver": "US",
    "atlanta": "US",
    "dallas": "US",
    # UK
    "london": "GB",
    "manchester": "GB",
    "edinburgh": "GB",
    # Other
    "toronto": "CA",
    "vancouver": "CA",
    "sydney": "AU",
    "melbourne": "AU",
    "berlin": "DE",
    "munich": "DE",
    "paris": "FR",
    "singapore": "SG",
    "amsterdam": "NL",
    "tokyo": "JP",
    "osaka": "JP",
    "dubai": "AE",
    "tel aviv": "IL",
}

# Known Indian state / region names
INDIA_STATES: dict[str, str] = {
    "karnataka": "Karnataka",
    "maharashtra": "Maharashtra",
    "delhi": "Delhi",
    "telangana": "Telangana",
    "tamil nadu": "Tamil Nadu",
    "west bengal": "West Bengal",
    "uttar pradesh": "Uttar Pradesh",
    "rajasthan": "Rajasthan",
    "gujarat": "Gujarat",
    "kerala": "Kerala",
    "andhra pradesh": "Andhra Pradesh",
    "punjab": "Punjab",
    "haryana": "Haryana",
    "odisha": "Odisha",
    "madhya pradesh": "Madhya Pradesh",
}

# City → region (for select known cities)
CITY_REGION: dict[str, str] = {
    "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "mysuru": "Karnataka", "mysore": "Karnataka",
    "mumbai": "Maharashtra", "pune": "Maharashtra",
    "hyderabad": "Telangana",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu",
    "kolkata": "West Bengal",
    "delhi": "Delhi", "new delhi": "Delhi", "noida": "Uttar Pradesh",
    "gurgaon": "Haryana", "gurugram": "Haryana",
    "jaipur": "Rajasthan",
    "ahmedabad": "Gujarat", "surat": "Gujarat",
    "kochi": "Kerala",
    "chandigarh": "Punjab",
    "manipal": "Karnataka",
}


def normalize_location(raw: str | None) -> Location:
    """Parse a raw location string into a structured Location."""
    if not raw:
        return Location()

    parts = [p.strip() for p in raw.split(",")]
    city = region = country_code = None

    # Walk parts right-to-left: last is most likely country, first is city
    for i, part in enumerate(reversed(parts)):
        key = part.lower()

        if country_code is None and key in COUNTRY_MAP:
            country_code = COUNTRY_MAP[key]

        elif region is None and key in INDIA_STATES:
            region = INDIA_STATES[key]

    # City = first part
    if parts:
        city = parts[0]
        city_key = city.lower()

        if country_code is None and city_key in CITY_COUNTRY:
            country_code = CITY_COUNTRY[city_key]

        if region is None and city_key in CITY_REGION:
            region = CITY_REGION[city_key]

    return Location(city=city or None, region=region, country=country_code)
