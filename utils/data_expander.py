"""
Dataset Expansion Utilities
---------------------------
Scripts to expand the medicine dataset by pulling data from:
  - OpenFDA drug API (https://api.fda.gov/drug/ndc.json)
  - Jan Aushadhi product list (manually curated from janaushadhi.gov.in)

Run this to refresh or extend the base dataset. Keeps the core app
decoupled from external API dependencies.
"""

import pandas as pd
import json
import time
from pathlib import Path


def fetch_openfda_sample(limit: int = 100):
    """Fetch a sample of drug records from OpenFDA.

    Note: OpenFDA is US-focused, so we use it primarily to validate
    composition strings and generic names. Indian pricing must come
    from local sources.
    """
    import urllib.request

    url = f"https://api.fda.gov/drug/ndc.json?limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("results", [])
    except Exception as e:
        print(f"OpenFDA fetch failed: {e}")
        return []


def validate_dataset(csv_path: str):
    """Sanity-check the medicines dataset. Returns a list of issues found."""
    df = pd.read_csv(csv_path)
    issues = []

    required_cols = [
        "brand_name", "generic_name", "composition", "strength",
        "branded_price", "generic_price", "jan_aushadhi_code",
    ]
    for col in required_cols:
        if col not in df.columns:
            issues.append(f"Missing column: {col}")

    # Generic price should always be less than branded price
    if "branded_price" in df.columns and "generic_price" in df.columns:
        bad_pricing = df[df["generic_price"] >= df["branded_price"]]
        if len(bad_pricing) > 0:
            issues.append(
                f"{len(bad_pricing)} rows have generic price >= branded price"
            )

    # Any missing values?
    for col in required_cols:
        if col in df.columns:
            n_missing = df[col].isna().sum()
            if n_missing > 0:
                issues.append(f"{n_missing} missing values in '{col}'")

    # Duplicates?
    dupes = df.duplicated(subset=["brand_name"]).sum()
    if dupes > 0:
        issues.append(f"{dupes} duplicate brand names")

    return issues


def generate_summary_stats(csv_path: str):
    """Quick overview of the dataset."""
    df = pd.read_csv(csv_path)

    avg_savings_pct = (
        (df["branded_price"] - df["generic_price"]) / df["branded_price"] * 100
    ).mean()

    stats = {
        "total_medicines": len(df),
        "therapeutic_classes": df["therapeutic_class"].nunique(),
        "avg_branded_price": round(df["branded_price"].mean(), 2),
        "avg_generic_price": round(df["generic_price"].mean(), 2),
        "avg_savings_percent": round(avg_savings_pct, 2),
        "total_manufacturers": df["manufacturer_brand"].nunique(),
    }
    return stats


if __name__ == "__main__":
    csv_path = Path(__file__).parent.parent / "data" / "medicines.csv"

    print("Validating dataset...")
    issues = validate_dataset(csv_path)
    if issues:
        print("Issues found:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("  All checks passed.")

    print("\nDataset statistics:")
    stats = generate_summary_stats(csv_path)
    for k, v in stats.items():
        print(f"  {k}: {v}")
