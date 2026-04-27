"""
Jan Aushadhi Store Locator
--------------------------
Finds the nearest Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP)
stores based on user location. Uses the haversine formula to calculate
distance — no API key required for the basic version.

If a Google Maps API key is provided, it can also return directions.
"""

import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres.

    The haversine formula treats the Earth as a sphere (close enough for
    city-scale distances). Returns the shortest distance 'as the crow flies'.
    """
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class StoreLocator:
    def __init__(self, data_path: str = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "jan_aushadhi_stores.csv"
        self.df = pd.read_csv(data_path)

    def find_nearest(self, user_lat: float, user_lon: float, n: int = 5):
        """Return the n nearest stores — vectorised with numpy for speed across 19K stores."""
        import numpy as np
        R = 6371
        lat1 = np.radians(user_lat)
        lon1 = np.radians(user_lon)
        lats = np.radians(self.df["latitude"].values)
        lons = np.radians(self.df["longitude"].values)
        dlat = lats - lat1
        dlon = lons - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lats)*np.sin(dlon/2)**2
        dists = R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        idx = np.argsort(dists)[:n]
        results = self.df.iloc[idx].copy()
        results["distance_km"] = np.round(dists[idx], 2)
        return results.to_dict("records")

    def find_by_city(self, city: str):
        mask = self.df["city"].str.lower() == city.lower()
        return self.df[mask].head(20).to_dict("records")

    def find_by_state(self, state: str):
        mask = self.df["state"].str.lower() == state.lower()
        return self.df[mask].head(50).to_dict("records")

    def find_by_pincode(self, pincode: str):
        """Return all stores matching a pincode."""
        mask = self.df["pincode"].astype(str) == str(pincode)
        return self.df[mask].to_dict("records")

    def get_all_cities(self):
        return sorted(self.df["city"].dropna().astype(str).unique().tolist())

    def get_all_states(self):
        return sorted(self.df["state"].dropna().astype(str).unique().tolist())

    def get_total_stores(self):
        return len(self.df)

    def get_directions_url(self, lat: float, lon: float):
        """Build a Google Maps directions URL — no API key needed."""
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"


# Pincode to approximate lat/lon lookup for major Indian cities.
# Used when we don't have the user's GPS coordinates.
PINCODE_APPROX = {
    "110": (28.6139, 77.2090),  # Delhi NCR
    "400": (19.0760, 72.8777),  # Mumbai
    "560": (12.9716, 77.5946),  # Bengaluru
    "600": (13.0827, 80.2707),  # Chennai
    "700": (22.5726, 88.3639),  # Kolkata
    "500": (17.3850, 78.4867),  # Hyderabad
    "380": (23.0225, 72.5714),  # Ahmedabad
    "411": (18.5204, 73.8567),  # Pune
    "302": (26.9124, 75.7873),  # Jaipur
    "226": (26.8467, 80.9462),  # Lucknow
    "141": (30.9010, 75.8573),  # Ludhiana
    "144": (31.3260, 75.5762),  # Jalandhar / Phagwara
    "160": (30.7333, 76.7794),  # Chandigarh
    "143": (31.6340, 74.8723),  # Amritsar
    "462": (23.2599, 77.4126),  # Bhopal
    "452": (22.7196, 75.8577),  # Indore
    "800": (25.5941, 85.1376),  # Patna
    "751": (20.2961, 85.8245),  # Bhubaneswar
    "682": (9.9312, 76.2673),   # Kochi
    "695": (8.5241, 76.9366),   # Trivandrum
    "781": (26.1445, 91.7362),  # Guwahati
    "248": (30.3165, 78.0322),  # Dehradun
    "440": (21.1458, 79.0882),  # Nagpur
    "395": (21.1702, 72.8311),  # Surat
    "390": (22.3072, 73.1812),  # Vadodara
    "641": (11.0168, 76.9558),  # Coimbatore
}


def pincode_to_coords(pincode: str):
    """Rough lat/lon lookup from the first 3 digits of a pincode."""
    if not pincode or len(str(pincode)) < 3:
        return None
    prefix = str(pincode)[:3]
    return PINCODE_APPROX.get(prefix)


if __name__ == "__main__":
    loc = StoreLocator()
    print(f"Total stores loaded: {loc.get_total_stores()}")

    # Ludhiana coordinates
    nearest = loc.find_nearest(30.9010, 75.8573, n=3)
    print("\nNearest stores to Ludhiana:")
    for s in nearest:
        print(f"  {s['store_name']} — {s['distance_km']} km away")
