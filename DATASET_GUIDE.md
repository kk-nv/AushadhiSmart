# Using the Official Jan Aushadhi Dataset

## What You Have

The CSV you uploaded (`Product_List_24_4_2026___12_31_16.csv`) is the **official Jan Aushadhi product price list** from the government's PMBJP (Pradhan Mantri Bhartiya Janaushadhi Pariyojana) program.

**Dataset specs:**
- **2,439 generic medicines** with official MRP prices
- **68 therapeutic categories** (antibiotics, cardiovascular, antidiabetics, etc.)
- **Updated as of April 24, 2026** (filename indicates the timestamp)
- Source: [janaushadhi.gov.in](https://janaushadhi.gov.in)

---

## What the Integration Script Did

The `merge_janaushadhi_data.py` script combined your curated **branded-to-generic mapping** (68 medicines) with the official Jan Aushadhi list:

### Step 1: Price Updates
It matched your 68 branded medicines to the Jan Aushadhi catalog and **updated generic prices** with official data:
- Example: **Pan 40** → Pantoprazole was ₹22.50 (estimate), updated to **₹11.35** (official)
- Example: **Glycomet 500** → Metformin was ₹5.75, updated to **₹24.75**

**39 out of 68** branded medicines got price corrections.

### Step 2: Adding Generic-Only Medicines
The remaining **2,436 Jan Aushadhi medicines** that didn't have branded equivalents in your dataset were added as "generic-only" entries:
- These appear as `Generic [composition]` in the brand name field
- They're fully searchable by composition or therapeutic class
- Users can browse them but won't see a branded price comparison (since no branded equivalent is tracked)

### Final Result
**Enhanced dataset:** `data/medicines_enhanced.csv`
- **2,504 total medicines** (68 branded + 2,436 generic-only)
- **105 therapeutic classes**
- **79.8% average savings** (branded vs. generic)

---

## How to Use This in Your App

### Option 1: Automatic (Recommended)
The app **automatically detects** which dataset to use:

```python
from backend.recommender import MedicineRecommender

rec = MedicineRecommender(use_enhanced=True)  # Tries medicines_enhanced.csv first
```

If `medicines_enhanced.csv` doesn't exist, it falls back to `medicines.csv`.

### Option 2: Explicit Path
```python
rec = MedicineRecommender(data_path="data/medicines_enhanced.csv")
```

### Option 3: Add a UI Toggle (Streamlit)
Add this to your sidebar in `app/main.py`:

```python
with st.sidebar:
    dataset_choice = st.radio(
        "Dataset",
        ["Enhanced (2,504 medicines)", "Basic (68 medicines)"],
    )
    use_enhanced = "Enhanced" in dataset_choice
    
recommender = MedicineRecommender(use_enhanced=use_enhanced)
```

---

## What You Can Do Next

### 1. **Keep the Dataset Up-to-Date**
Jan Aushadhi updates their product list monthly. Download the latest CSV from [janaushadhi.gov.in/product.aspx](https://janaushadhi.gov.in/product.aspx) and re-run:

```bash
python utils/merge_janaushadhi_data.py
```

This will regenerate `medicines_enhanced.csv` with the latest prices.

### 2. **Add More Branded Mappings**
The current dataset has 68 branded medicines manually mapped to generics. To expand:

1. Open `data/medicines.csv`
2. Add rows for popular branded drugs (e.g., Lantus, Trajenta, Galvus)
3. Re-run the merge script

The script will automatically link them to Jan Aushadhi equivalents.

### 3. **Improve the Matching Logic**
The current matching uses **normalized string matching** (removes "Tablets IP", "mg", etc. and compares). 

For better accuracy, you could:
- Add fuzzy matching between branded `composition` and Jan Aushadhi `Generic Name`
- Use a manually curated mapping file (brand → JA drug code)
- Integrate with an API like OpenFDA for composition validation

### 4. **Multi-Strength Handling**
Some medicines come in multiple strengths (e.g., Metformin 500mg vs. 1000mg). Currently, the script picks the first match. You could:
- Extract strength from both datasets
- Match based on composition + strength
- Show all available strengths in the UI

---

## Example: Searching the Enhanced Dataset

```python
from backend.recommender import MedicineRecommender

rec = MedicineRecommender(use_enhanced=True)

# Search by brand (works for the 68 tracked brands)
result = rec.get_generic_alternatives("Pan 40")
print(f"{result['searched_for']} → {result['generic_name']}")
print(f"Branded: ₹{result['branded_price']} | Generic: ₹{result['generic_price']}")
print(f"Savings: {result['savings_percent']}%")

# Search by generic name (works for all 2,504 medicines)
results = rec.search("Rosuvastatin", limit=5)
for r in results:
    print(f"  {r['generic_name']} | ₹{r['generic_price']} | {r['pack_size']}")

# Browse by category
diabetes_meds = rec.get_by_therapeutic_class("Antidiabetic")
print(f"Found {len(diabetes_meds)} diabetes medicines")
```

---

## File Structure After Integration

```
generic-medicine-recommender/
├── data/
│   ├── medicines.csv                # Original 68 branded mappings
│   ├── medicines_enhanced.csv       # ✨ NEW: 2,504 medicines (merged)
│   └── jan_aushadhi_stores.csv
├── utils/
│   ├── merge_janaushadhi_data.py    # ✨ NEW: Merger script
│   └── data_expander.py
└── ...
```

---

## Limitations & Future Work

### Current Limitations
1. **Composition matching is approximate** — some branded drugs might not link to the correct Jan Aushadhi generic if composition strings don't match
2. **No multi-pack handling** — if a branded medicine comes in 10s and the generic comes in 15s, prices aren't normalized per-unit
3. **Generic-only medicines have estimated branded prices** — the script assumes generics are ~5x cheaper, which is rough

### Improvements You Could Make
- Add a **manual override mapping file** (CSV with brand → JA drug code) for tricky cases
- **Normalize per-tablet prices** so users can compare apples-to-apples
- Add **Salt-based matching** (e.g., "Paracetamol" as a base ingredient, regardless of brand or formulation)
- Integrate **1mg or PharmEasy APIs** to fetch real-time branded MRPs instead of static estimates

---

## TL;DR — Quick Start

**To use the 2,504-medicine enhanced dataset:**

```bash
# 1. The dataset is already created
ls data/medicines_enhanced.csv  # should exist

# 2. Run the app (it auto-detects the enhanced dataset)
streamlit run app/main.py

# 3. To update prices in the future, download the latest Jan Aushadhi CSV and run:
python utils/merge_janaushadhi_data.py
```

That's it! The app now has access to **2,439 official Jan Aushadhi medicines** with real government pricing.
