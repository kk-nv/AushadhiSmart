"""
Dataset Integration Script
---------------------------
Merges the curated branded-to-generic mapping (medicines.csv) with the 
official Jan Aushadhi product list (Product_List_24_4_2026___12_31_16.csv).

This creates an enhanced dataset where:
1. Branded medicines from medicines.csv are preserved
2. Jan Aushadhi prices are updated with official data
3. All 2,439 Jan Aushadhi generics become searchable
"""

import pandas as pd
import re
from pathlib import Path


def normalize_composition(text):
    """Clean up composition strings for matching.
    
    Example: 
      'Paracetamol 500mg' -> 'paracetamol 500'
      'Paracetamol Tablets IP 500 mg' -> 'paracetamol 500'
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove common pharma terms
    text = re.sub(r'\b(tablets?|capsules?|syrup|injection|gel|cream|ointment)\b', '', text)
    text = re.sub(r'\b(ip|bp|usp)\b', '', text)
    
    # Normalize 'mg' spacing: '500mg' -> '500'
    text = re.sub(r'(\d+)\s*mg', r'\1', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def extract_strength_from_generic_name(name):
    """Extract strength/dosage from Jan Aushadhi generic name.
    
    Example: 'Paracetamol Tablets IP 500 mg' -> '500mg'
    """
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*mg', name, re.IGNORECASE)
    if matches:
        return f"{matches[0]}mg"
    
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*mcg', name, re.IGNORECASE)
    if matches:
        return f"{matches[0]}mcg"
    
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', name)
    if matches:
        return f"{matches[0]}%"
    
    return ""


def merge_datasets(branded_csv, janaushadhi_csv, output_csv):
    """Create the merged dataset."""
    
    # Load both datasets
    branded = pd.read_csv(branded_csv)
    ja = pd.read_csv(janaushadhi_csv)
    
    print(f"Loaded {len(branded)} branded medicines")
    print(f"Loaded {len(ja)} Jan Aushadhi medicines")
    
    # Normalize the Jan Aushadhi data
    ja['normalized_name'] = ja['Generic Name'].apply(normalize_composition)
    ja['strength'] = ja['Generic Name'].apply(extract_strength_from_generic_name)
    
    # For each branded medicine, try to find a match in the Jan Aushadhi list
    ja_price_updates = 0
    for idx, row in branded.iterrows():
        normalized = normalize_composition(row['composition'])
        
        # Try to find matching Jan Aushadhi product
        matches = ja[ja['normalized_name'].str.contains(normalized, na=False, regex=False)]
        
        if len(matches) > 0:
            # Use the first match (could be improved with fuzzy scoring)
            ja_match = matches.iloc[0]
            
            # Update the Jan Aushadhi price if it's different
            if branded.loc[idx, 'generic_price'] != ja_match['MRP']:
                print(f"  Updated {row['brand_name']}: ₹{row['generic_price']} -> ₹{ja_match['MRP']}")
                branded.loc[idx, 'generic_price'] = ja_match['MRP']
                branded.loc[idx, 'jan_aushadhi_code'] = f"JA{ja_match['Drug Code']:04d}"
                ja_price_updates += 1
    
    print(f"\nUpdated {ja_price_updates} Jan Aushadhi prices")
    
    # Now add all the Jan Aushadhi medicines that aren't already in the branded list
    # These won't have branded equivalents, but users can still search by generic name
    
    new_generics = []
    for _, ja_row in ja.iterrows():
        # Check if this generic is already covered
        normalized = ja_row['normalized_name']
        already_exists = branded['composition'].apply(normalize_composition).str.contains(
            normalized, na=False, regex=False
        ).any()
        
        if not already_exists and normalized.strip():
            # Add as a new row with no branded equivalent
            new_generics.append({
                'brand_name': f"Generic {ja_row['Generic Name'][:30]}",  # truncate long names
                'generic_name': ja_row['Generic Name'],
                'composition': ja_row['Generic Name'],
                'strength': ja_row['strength'] or "varies",
                'dosage_form': 'Tablet' if 'tablet' in ja_row['Generic Name'].lower() else 'Various',
                'therapeutic_class': ja_row['Group Name'],
                'indication': ja_row['Group Name'],
                'branded_price': ja_row['MRP'] * 5,  # estimate: generics are ~5x cheaper
                'generic_price': ja_row['MRP'],
                'pack_size': ja_row['Unit Size'],
                'manufacturer_brand': 'Jan Aushadhi',
                'jan_aushadhi_code': f"JA{ja_row['Drug Code']:04d}",
            })
    
    print(f"\nAdding {len(new_generics)} new generic-only medicines")
    
    # Combine
    enhanced = pd.concat([branded, pd.DataFrame(new_generics)], ignore_index=True)
    
    # Save
    enhanced.to_csv(output_csv, index=False)
    print(f"\n✅ Enhanced dataset saved to {output_csv}")
    print(f"   Total medicines: {len(enhanced)}")
    print(f"   Therapeutic classes: {enhanced['therapeutic_class'].nunique()}")
    
    return enhanced


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    
    branded_csv = project_root / "data" / "medicines.csv"
    ja_csv = "/mnt/user-data/uploads/Product_List_24_4_2026___12_31_16.csv"
    output_csv = project_root / "data" / "medicines_enhanced.csv"
    
    enhanced = merge_datasets(branded_csv, ja_csv, output_csv)
    
    # Show some stats
    print("\n📊 Enhanced dataset statistics:")
    print(f"   Avg branded price: ₹{enhanced['branded_price'].mean():.2f}")
    print(f"   Avg generic price: ₹{enhanced['generic_price'].mean():.2f}")
    
    savings_pct = (
        (enhanced['branded_price'] - enhanced['generic_price']) 
        / enhanced['branded_price'] * 100
    ).mean()
    print(f"   Avg savings: {savings_pct:.1f}%")
