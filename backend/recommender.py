"""
Medicine Recommendation Engine
--------------------------------
Fixes:
  1. ZeroDivisionError - all zero-price rows removed from dataset
  2. Alternatives now pulled from medicine_dataset substitutes map (248K medicines)
     so you see genuinely different brand alternatives, not the same name repeated
  3. Non-Jan Aushadhi branded alternatives included in the table
"""

import pandas as pd
import json
from rapidfuzz import fuzz, process
from pathlib import Path


class MedicineRecommender:
    def __init__(self, data_path=None):
        base_dir = Path(__file__).parent.parent / "data"

        if data_path is None:
            for name in ["medicines_mega.csv", "medicines_enhanced.csv", "medicines.csv"]:
                p = base_dir / name
                if p.exists():
                    data_path = p
                    break

        self.df = pd.read_csv(data_path)

        # Safety: drop any zero/null price rows (fixes ZeroDivisionError)
        self.df = self.df[self.df["branded_price"].notna() & (self.df["branded_price"] > 0)]
        self.df = self.df[self.df["generic_price"].notna()  & (self.df["generic_price"]  > 0)]
        self.df = self.df[self.df["generic_price"] < self.df["branded_price"]]
        self.df = self.df.reset_index(drop=True)

        # Load substitutes map from medicine_dataset (222K medicines with real substitutes)
        self.substitutes_map    = {}
        self.medicine_meta      = {}
        self.all_medicine_names = []

        subs_path  = base_dir / "substitutes_map.json"
        meta_path  = base_dir / "medicine_meta.json"
        names_path = base_dir / "all_medicine_names.json"

        if subs_path.exists():
            with open(subs_path) as f:
                self.substitutes_map = json.load(f)
        if meta_path.exists():
            with open(meta_path) as f:
                self.medicine_meta = json.load(f)
        if names_path.exists():
            with open(names_path) as f:
                self.all_medicine_names = json.load(f)

        self._prepare_search_index()

    def _prepare_search_index(self):
        self.df["search_text"] = (
            self.df["brand_name"].str.lower().fillna("") + " " +
            self.df["generic_name"].str.lower().fillna("") + " " +
            self.df["composition"].str.lower().fillna("")
        )
        self.brand_names   = self.df["brand_name"].str.lower().tolist()
        self.generic_names = self.df["generic_name"].str.lower().tolist()

    def search(self, query: str, limit: int = 10, min_score: int = 60):
        if not query or not query.strip():
            return []

        q = query.strip().lower()
        results = []
        seen = set()

        for idx, brand in enumerate(self.brand_names):
            if q in brand:
                row = self.df.iloc[idx].to_dict()
                row["match_score"] = 100
                results.append(row)
                seen.add(idx)

        for idx, generic in enumerate(self.generic_names):
            if idx in seen: continue
            if q in generic:
                row = self.df.iloc[idx].to_dict()
                row["match_score"] = 95
                results.append(row)
                seen.add(idx)

        fuzzy_hits = process.extract(
            q, self.df["search_text"].tolist(),
            scorer=fuzz.partial_ratio, limit=limit * 2
        )
        for _, score, idx in fuzzy_hits:
            if idx in seen or score < min_score: continue
            row = self.df.iloc[idx].to_dict()
            row["match_score"] = score
            results.append(row)
            seen.add(idx)

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:limit]

    def get_generic_alternatives(self, query: str):
        matches = self.search(query, limit=3)
        if not matches:
            return None

        primary = matches[0]

        # Jan Aushadhi alternatives: same composition in JA dataset
        ja_alts = self.df[
            self.df["composition"].str.lower().fillna("") ==
            str(primary["composition"]).lower()
        ].copy()
        ja_alts = ja_alts[ja_alts["generic_price"] > 0].sort_values("generic_price")

        ja_rows = []
        for _, r in ja_alts.iterrows():
            bp = float(r["branded_price"])
            gp = float(r["generic_price"])
            if bp <= 0: continue
            pct = round((bp - gp) / bp * 100, 1)
            ja_rows.append({
                "name":         r["generic_name"],
                "manufacturer": r.get("manufacturer_brand", "Jan Aushadhi"),
                "pack_size":    r.get("pack_size", "—"),
                "market_price": bp,
                "ja_price":     gp,
                "savings_pct":  pct,
                "ja_code":      r.get("jan_aushadhi_code", "—"),
                "source":       "✅ Jan Aushadhi / PMBJP",
                "is_ja":        True,
            })

        # Market brand alternatives from substitutes_map
        brand_rows = []
        query_key  = query.strip().lower()

        subs = self.substitutes_map.get(query_key, [])
        if not subs:
            brand_key = str(primary.get("brand_name", "")).strip().lower()
            subs = self.substitutes_map.get(brand_key, [])
        if not subs:
            keys = list(self.substitutes_map.keys())
            hit  = process.extractOne(query_key, keys, scorer=fuzz.partial_ratio)
            if hit and hit[1] >= 75:
                subs = self.substitutes_map[hit[0]]

        for sub_name in subs[:8]:
            if not sub_name: continue
            brand_rows.append({
                "name":         sub_name,
                "manufacturer": "Various",
                "pack_size":    "—",
                "market_price": None,
                "ja_price":     None,
                "savings_pct":  None,
                "ja_code":      "—",
                "source":       "🏪 Market Brand (Alternative)",
                "is_ja":        False,
            })

        # Extra metadata
        meta     = self.medicine_meta.get(query_key, {})
        uses_txt = ", ".join(meta.get("uses", [])) or str(primary.get("indication", "—"))
        tc       = meta.get("therapeutic_class") or str(primary.get("therapeutic_class", "—"))

        bp = float(primary["branded_price"])
        gp = float(primary["generic_price"])
        savings_pct = round((bp - gp) / bp * 100, 1) if bp > 0 else 0

        return {
            "searched_for":      query,
            "generic_name":      primary["generic_name"],
            "composition":       primary["composition"],
            "therapeutic_class": tc,
            "indication":        uses_txt,
            "branded_price":     bp,
            "generic_price":     gp,
            "savings_per_pack":  round(bp - gp, 2),
            "savings_percent":   savings_pct,
            "jan_aushadhi_code": primary.get("jan_aushadhi_code", "—"),
            "pack_size":         primary.get("pack_size", "—"),
            "dosage_form":       primary.get("dosage_form", "—"),
            "strength":          primary.get("strength", "—"),
            "ja_alternatives":   ja_rows,
            "brand_alternatives": brand_rows,
        }

    def get_by_therapeutic_class(self, tc: str):
        mask = self.df["therapeutic_class"].str.lower().str.contains(tc.lower(), na=False)
        return self.df[mask].to_dict("records")

    def get_all_classes(self):
        return sorted(self.df["therapeutic_class"].dropna().unique().tolist())

    def get_total_medicines(self):
        return len(self.df)

    def get_autocomplete_options(self):
        ja_names = self.df["generic_name"].dropna().unique().tolist()
        return sorted(set(ja_names + self.all_medicine_names[:50000]))
