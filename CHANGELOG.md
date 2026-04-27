# Changelog

All notable changes to the Generic Medicine Recommender project.

---

## [v2.0] - 2026-04-24 - Enhanced Dataset + Autocomplete

### 🎯 Major Changes

#### 1. **Removed Brand Names - Focus on Generic Medicines**
- **Before:** App showed branded medicine names (Crocin, Pan 40, Dolo 650, etc.)
- **After:** App focuses entirely on generic names (Paracetamol, Pantoprazole, Metformin)
- **Why:** Aligns with Jan Aushadhi's mission of promoting generics, removes commercial bias

#### 2. **YouTube-Style Autocomplete Search**
- **New Component:** `app/autocomplete.py` 
- **Behavior:** As you type, dropdown filters and shows matching medicines
- **Example:** Type "para" → instantly see "Paracetamol", "Paracetamol + Ibuprofen", etc.
- **Limit:** Shows top 20 matches to keep dropdown fast

#### 3. **Official Jan Aushadhi Dataset Integration (2,439 medicines)**
- **Source:** `Product_List_24_4_2026___12_31_16.csv` from janaushadhi.gov.in
- **Before:** 68 medicines with estimated prices
- **After:** 2,504 medicines with official government MRPs
- **Script:** `utils/merge_janaushadhi_data.py` handles integration
- **Price Updates:** 39 medicines got official price corrections

### 📊 Dataset Statistics

| Metric | Before (v1.0) | After (v2.0) |
|--------|---------------|--------------|
| Total medicines | 68 | 2,504 |
| Therapeutic classes | 37 | 105 |
| Data source | Manual curation | Official Jan Aushadhi catalog |
| Price accuracy | Estimated | Government-verified MRP |
| Avg savings | 78.85% | 79.8% |

### 🔧 Technical Changes

#### New Files
- `app/autocomplete.py` — Custom autocomplete search component
- `utils/merge_janaushadhi_data.py` — Dataset integration script
- `data/medicines_enhanced.csv` — 2,504 medicines (merged dataset)
- `DATASET_GUIDE.md` — Documentation for using official data
- `CHANGELOG.md` — This file

#### Modified Files
- `app/main.py` — Replaced brand-centric UI with generic-focused design
- `backend/recommender.py` — Auto-detects enhanced vs. basic dataset
- `README.md` — Updated to reflect new features

#### UI Changes
- **Search box:** Plain text input → Autocomplete with live filtering
- **Price labels:** "Branded Price" → "Market Price (Branded)"
- **Price labels:** "Generic Price" → "Jan Aushadhi Price"
- **Tables:** Removed "Brand" column everywhere, kept only "Generic Name"
- **Savings calculator:** Changed from brand-based to generic-based selection

### 🚀 Performance Impact
- **Autocomplete:** Filters 2,504+ entries client-side (instant)
- **Dataset load:** ~0.5 seconds to load 2,504 rows via Pandas
- **Search:** Still uses 3-tier matching (exact → substring → fuzzy)
- **Memory:** ~2 MB increase (enhanced CSV is 141 KB vs. basic 9 KB)

### 📝 Migration Guide

If you're upgrading from v1.0:

1. **Pull latest code**
2. **Run the merger** (if you have the Jan Aushadhi CSV):
   ```bash
   python utils/merge_janaushadhi_data.py
   ```
3. **Restart Streamlit** — app auto-detects `medicines_enhanced.csv`

**Backwards compatibility:** If `medicines_enhanced.csv` doesn't exist, the app falls back to the original 68-medicine dataset.

---

## [v1.0] - 2026-04-24 - Initial Release

### Features
- Fuzzy search for branded medicines (68 curated entries)
- Price comparison: branded vs. generic
- Jan Aushadhi store locator (50 stores across India)
- Savings calculator with 10-year projections
- Browse by 37 therapeutic classes
- Interactive Folium maps

### Tech Stack
- Python 3.11
- Streamlit 1.31+
- Pandas, RapidFuzz, Plotly, Folium

---

## Versioning

Format: `[Major.Minor]`
- **Major** = Breaking changes or major feature additions
- **Minor** = Bug fixes, small enhancements, dataset updates
