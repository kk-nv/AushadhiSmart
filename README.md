# 💊 Generic Medicine Recommender for India

A full-stack Python application that helps Indian households save money on medicines by finding generic alternatives to expensive branded drugs, and locating the nearest Jan Aushadhi store to buy them.

---

## The Problem

Indians spend over **₹1.8 lakh crore** on medicines every year. Branded medicines often cost **5 to 10 times more** than their generic equivalents — even though the active molecule, dosage, and efficacy are identical.

The Government of India runs the **Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP)**, which operates over **14,000 Jan Aushadhi Kendras** nationwide selling quality-tested generics at 50–90% lower prices. But most people don't know about it.

**This app closes that awareness gap.**

---

## What It Does

1. **Search any medicine** by generic name with YouTube-style autocomplete (filters as you type)
2. **See the Jan Aushadhi price** and compare it to typical market prices
3. **Project household savings** over months, years, and a lifetime
4. **Locate the nearest Jan Aushadhi store** by pincode, city, or GPS coordinates
5. **Browse by therapeutic class** for doctors, pharmacists, and students
6. **Build a household medicine list** to calculate total monthly/yearly savings

**Focus on generic medicines only** — no brand names, just the active ingredients and official Jan Aushadhi pricing.

---

## Screenshots / Features

| Page | What it does |
|------|--------------|
| 🔍 Find Generic Alternative | **Autocomplete search** (filters as you type) → composition, price comparison chart, 10-year savings |
| 📍 Nearest Jan Aushadhi Store | Interactive Folium map with pins for 50 stores across India |
| 📊 Browse by Category | 105 therapeutic classes with all Jan Aushadhi medicines |
| 💰 Savings Calculator | Multi-medicine cart with total household savings |
| ℹ️ About | Problem statement, tech stack, disclaimers |

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Streamlit | Fastest way to ship a data app with a polished UI |
| Fuzzy Search | RapidFuzz | Handles typos like "Crosin" → Crocin, "paracetmol" → Paracetamol |
| Data | Pandas + CSV | Transparent, easy to extend, no database dependency |
| Charts | Plotly | Interactive price-comparison bars |
| Maps | Folium (Leaflet.js) | Interactive store markers, no API key needed |
| Distance | Haversine formula | Great-circle distance — no Google Maps API required |

---

## Project Structure

```
generic-medicine-recommender/
├── app/
│   └── main.py                   # Streamlit UI (5 pages)
├── backend/
│   ├── recommender.py            # Fuzzy-match search + generic lookup
│   └── store_locator.py          # Jan Aushadhi store finder
├── data/
│   ├── medicines.csv             # 68 curated medicines with branded + generic prices
│   └── jan_aushadhi_stores.csv   # 50 PMBJP Kendras across India
├── utils/
│   └── data_expander.py          # OpenFDA integration + dataset validator
├── requirements.txt
└── README.md
```

---

## Setup & Run

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd generic-medicine-recommender
pip install -r requirements.txt
```

### 2. Launch the Streamlit app

```bash
streamlit run app/main.py
```

Open **http://localhost:8501** in your browser. That's it.

### 3. (Optional) Validate the dataset

```bash
python utils/data_expander.py
```

Output:
```
Validating dataset...
  All checks passed.

Dataset statistics:
  total_medicines: 68
  therapeutic_classes: 37
  avg_branded_price: 100.65
  avg_generic_price: 23.10
  avg_savings_percent: 78.85
```

---

## How the Matching Engine Works

The recommender does three passes in order of precision:

1. **Exact substring match on brand name** — if you type "crocin" and "Crocin" exists, it wins instantly (score 100)
2. **Exact substring match on generic name** — e.g. searching "paracetamol" matches all paracetamol brands (score 95)
3. **Fuzzy match using RapidFuzz** — handles typos by comparing partial-ratio scores against a combined search index (brand + generic + composition). Minimum score threshold: 60.

Once a match is found, `get_generic_alternatives()` pulls **all rows with the same composition** so the user sees every brand selling that molecule — sorted by price.

---

## Sample Results

| Generic Medicine | Market Price (Est.) | Jan Aushadhi Price | You Save |
|------------------|---------------------|-------------------|----------|
| Paracetamol 500mg | ₹30.00 | ₹9.38 | 68.7% |
| Pantoprazole 40mg | ₹145.00 | ₹11.35 | 92.2% |
| Metformin 500mg | ₹123.75 | ₹24.75 | 80.0% |
| Atorvastatin 10mg | ₹66.25 | ₹8.25 | 87.5% |
| Levothyroxine 50mcg | ₹120.00 | ₹24.00 | 80.0% |

A household buying 2 packs/month of Pantoprazole saves **₹3,216 per year** — over 10 years, that's ₹32,160 for a single medicine.

---

## Extending the Dataset

The `data/medicines.csv` file has 68 hand-curated entries covering the most common therapeutic classes in India. To add more:

1. Open `data/medicines.csv` in Excel or any text editor
2. Append rows with the same schema:
   ```
   brand_name, generic_name, composition, strength, dosage_form,
   therapeutic_class, indication, branded_price, generic_price,
   pack_size, manufacturer_brand, jan_aushadhi_code
   ```
3. Run `python utils/data_expander.py` to validate
4. Restart Streamlit — the cache reloads automatically

For bulk expansion, `utils/data_expander.py` includes a `fetch_openfda_sample()` function that pulls from the OpenFDA NDC API.

---

## Data Sources

- **Jan Aushadhi store list:** Compiled from [janaushadhi.gov.in](https://janaushadhi.gov.in) store directory
- **Branded medicine prices:** Publicly listed MRPs from Indian pharmacy chains (1mg, PharmEasy, NetMeds)
- **Generic medicine prices:** PMBJP product price list
- **Drug composition validation:** [OpenFDA NDC API](https://open.fda.gov/apis/drug/ndc/)

---

## Roadmap (Future Work)

- [ ] Add OCR so users can upload a prescription photo and get alternatives for all listed medicines
- [ ] Expand to 500+ medicines covering all 13 essential drug categories
- [ ] Integrate real-time pricing from 1mg/PharmEasy APIs for branded comparison
- [ ] Add Hindi, Tamil, Bengali UI for wider reach
- [ ] Deploy to Streamlit Cloud for public access
- [ ] Add a REST API layer (FastAPI) so other apps can consume the engine

---

## Disclaimer

This is an **informational tool only**. Generic medicines sold at Jan Aushadhi Kendras are approved by the CDSCO (Central Drugs Standard Control Organisation) and are bioequivalent to branded versions.

However, **always consult your doctor or pharmacist** before switching medications — especially for:
- Chronic conditions (diabetes, hypertension, thyroid)
- Narrow therapeutic index drugs (warfarin, phenytoin, lithium)
- Any medicine where brand-specific formulation matters

The author makes no medical claims and assumes no liability for decisions made based on this tool.

---

## License

MIT — free to use, modify, and redistribute. If you build on top of this, a credit link back is appreciated but not required.

---

## Credits

Built as a public-good project to raise awareness about affordable healthcare in India.

Data compiled from open government sources. No personal data is collected or transmitted.
