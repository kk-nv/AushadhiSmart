import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from backend.recommender import MedicineRecommender
from backend.store_locator import StoreLocator, pincode_to_coords

st.set_page_config(
    page_title="Jan Aushadhi — Generic Medicine Finder",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def load_engines():
    return MedicineRecommender(), StoreLocator()

recommender, locator = load_engines()

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Core metric fix for BOTH light and dark mode ── */
[data-testid="stMetric"] {
    background: transparent !important;
    border: 1.5px solid rgba(128,128,128,0.3) !important;
    border-left: 4px solid #006838 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] p {
    color: #888 !important;
    font-size: 0.85rem !important;
}
[data-testid="stMetricValue"] > div {
    color: inherit !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] > div { font-size: 0.82rem !important; }

/* ── Price text ── */
.price-red   { color:#e53935; font-size:1.9rem; font-weight:800; }
.price-green { color:#2e7d32; font-size:1.9rem; font-weight:800; }
.price-orange{ color:#e65100; font-size:1.9rem; font-weight:800; }

/* ── Medicine description card ── */
.drug-card {
    background: linear-gradient(135deg,#e8f5e9,#f1f8e9);
    border-left: 5px solid #006838;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0 1rem 0;
}
.drug-card-dark {
    background: linear-gradient(135deg,rgba(0,104,56,.12),rgba(0,104,56,.06));
    border-left: 5px solid #2e7d32;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0 1rem 0;
}
@media (prefers-color-scheme:dark){
    .drug-card { background:linear-gradient(135deg,rgba(0,104,56,.15),rgba(0,104,56,.07)) !important;
                 color:#e0e0e0 !important; }
}

/* ── Savings box ── */
.savings-box {
    background: linear-gradient(135deg,#e8f5e9,#c8e6c9);
    border-left: 5px solid #006838;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    font-size: 1.05rem;
}
@media (prefers-color-scheme:dark){
    .savings-box { background:rgba(0,104,56,.18) !important; color:#e0e0e0 !important; }
}

/* ── Know Your Drug tabs ── */
.drug-section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #006838;
    border-bottom: 2px solid #a5d6a7;
    padding-bottom: 4px;
    margin: 1rem 0 0.5rem 0;
}
.pill-use {
    display:inline-block; background:#e8f5e9; color:#1b5e20;
    border:1px solid #a5d6a7; border-radius:20px;
    padding:4px 14px; margin:4px 5px 4px 0; font-size:.85rem; font-weight:600;
}
.pill-se {
    display:inline-block; background:#fce4ec; color:#880e4f;
    border:1px solid #f48fb1; border-radius:20px;
    padding:4px 14px; margin:4px 5px 4px 0; font-size:.85rem;
}
.badge {
    display:inline-block; background:#006838; color:#fff;
    border-radius:6px; padding:3px 10px; font-size:.78rem;
    font-weight:700; margin-right:6px;
}
.badge-orange {
    display:inline-block; background:#e65100; color:#fff;
    border-radius:6px; padding:3px 10px; font-size:.78rem;
    font-weight:700; margin-right:6px;
}
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:.5rem 0 1rem 0">
        <div style="font-size:2rem">🏥</div>
        <div style="font-size:1.1rem;font-weight:800;color:#006838">Jan Aushadhi</div>
        <div style="font-size:.75rem;color:#F7941D;font-weight:700">
            PMBJP — Pradhan Mantri Bhartiya<br>Janaushadhi Pariyojana
        </div>
        <hr style="border-color:#a5d6a7;margin:.7rem 0">
        <div style="font-size:.82rem;font-style:italic;opacity:.7">"Sasta Bhi, Achha Bhi"</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "🔍 Find Generic Alternative",
        "🧬 Know Your Drug",
        "📍 Nearest Jan Aushadhi Store",
        "📊 Browse by Category",
        "💰 Savings Calculator",
        "ℹ️ About",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("#### 📊 Database")
    st.metric("Medicines in DB", f"{recommender.get_total_medicines():,}")
    st.metric("Jan Aushadhi Stores", f"{locator.get_total_stores():,}")
    st.metric("States Covered", locator.df['state'].nunique())
    st.markdown("---")
    st.caption("⚠️ Always consult your doctor before switching medicines.")


# ── PAGE 1: Find Generic Alternative ─────────────────────────────────────────
if page == "🔍 Find Generic Alternative":
    st.markdown("## 🏥 Find Your Jan Aushadhi Generic")
    st.markdown("Search any branded or generic medicine name to find cheaper PMBJP alternatives.")

    if 'autocomplete_options' not in st.session_state:
        st.session_state.autocomplete_options = recommender.get_autocomplete_options()

    query = st.selectbox(
        "Medicine name",
        options=[""] + st.session_state.autocomplete_options,
        index=0,
        key="medicine_search",
        label_visibility="collapsed",
        placeholder="Type medicine name e.g. Paracetamol, Augmentin 625, Metformin...",
    )
    st.caption("💡 Just start typing — the dropdown filters automatically")

    if query:
        result = recommender.get_generic_alternatives(query)

        if not result:
            st.warning(f"No matches found for '{query}'. Try the generic salt name.")
        else:
            # ── Medicine header ──────────────────────────────────────────────
            st.markdown("---")
            st.markdown(f"## 💊 {result['generic_name']}")

            # Description card
            st.markdown(f"""
<div class="drug-card">
    <b>Active Salt / Composition:</b> {result['composition']}<br>
    <b>Used For:</b> {str(result['indication'])[:120]}<br>
    <b>Category:</b> {result['therapeutic_class']} &nbsp;
    <b>Form:</b> {result['dosage_form']} &nbsp;
    <b>Strength:</b> {result['strength']}
</div>""", unsafe_allow_html=True)

            # Metric row
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Strength",          result['strength'])
            c2.metric("Dosage Form",       result['dosage_form'])
            c3.metric("Therapeutic Class", str(result['therapeutic_class'])[:22])
            c4.metric("Pack Size",         result.get('pack_size','—'))

            st.markdown("---")

            # ── Cheapest Jan Aushadhi highlight ──────────────────────────────
            ja_alts = result["ja_alternatives"]
            if ja_alts:
                cheapest = ja_alts[0]
                avg_market = result["branded_price"]

                st.markdown("### 💰 Cheapest Jan Aushadhi Option")
                h1, h2, h3 = st.columns(3)
                with h1:
                    st.markdown("**🏆 Jan Aushadhi Price**")
                    st.markdown(f'<p class="price-green">₹{cheapest["ja_price"]:.2f}</p>', unsafe_allow_html=True)
                    st.caption(f"Pack: {cheapest['pack_size']}   |   JA Code: {cheapest['ja_code']}")
                with h2:
                    st.markdown("**🏪 Typical Market Price**")
                    st.markdown(f'<p class="price-red">₹{avg_market:.2f}</p>', unsafe_allow_html=True)
                    st.caption("Branded medicine price")
                with h3:
                    st.markdown("**💵 You Save**")
                    st.markdown(f'<p class="price-orange">{cheapest["savings_pct"]:.1f}%</p>', unsafe_allow_html=True)
                    st.caption(f"₹{avg_market - cheapest['ja_price']:.2f} per pack")
            else:
                cheapest = {"ja_price": result["generic_price"]}
                avg_market = result["branded_price"]

            st.markdown("---")

            # ── TABLE 1: Jan Aushadhi options ────────────────────────────────
            st.markdown("### ✅ Jan Aushadhi / PMBJP Options (Same Salt)")
            st.caption("Government-approved generic medicines — same active ingredient, sold at Jan Aushadhi Kendras")

            if ja_alts:
                ja_df = pd.DataFrame([{
                    "Generic Name":      r["name"],
                    "Manufacturer":      r["manufacturer"],
                    "Pack":              r["pack_size"],
                    "Market Price (₹)":  f"₹{r['market_price']:.2f}",
                    "JA Price (₹)":      f"₹{r['ja_price']:.2f}",
                    "Savings %":         f"{r['savings_pct']:.0f}%",
                    "JA Code":           r["ja_code"],
                } for r in ja_alts])

                def hl(row):
                    return ['background-color:#c8e6c9;color:#1b5e20'] * len(row) if row.name == 0 else [''] * len(row)

                st.dataframe(ja_df.style.apply(hl, axis=1),
                             use_container_width=True, hide_index=True,
                             height=min(380, len(ja_alts)*35+40))
                st.success("🟢 Green row = cheapest option. All rows have the SAME active salt — therapeutically identical.")
            else:
                st.info("No Jan Aushadhi price data found. Ask at your nearest Kendra.")

            # ── TABLE 2: Market brand alternatives ───────────────────────────
            brand_alts = result["brand_alternatives"]
            if brand_alts:
                st.markdown("---")
                st.markdown("### 🏪 Market Brand Alternatives (Same Salt)")
                st.caption("Other branded medicines with the same composition — available at market pharmacies")
                brand_df = pd.DataFrame([{
                    "Brand Name":  r["name"],
                    "Manufacturer": r["manufacturer"],
                } for r in brand_alts])
                st.dataframe(brand_df, use_container_width=True, hide_index=True)
                st.info("💡 These are equivalent brands — but Jan Aushadhi options above are significantly cheaper.")

            # ── Savings calculator ───────────────────────────────────────────
            st.markdown("---")
            st.markdown("### 📈 Household Savings Calculator")

            sc1, sc2 = st.columns([2, 3])
            with sc1:
                packs = st.slider("Packs per month", 1, 10, 2)
            with sc2:
                jp = cheapest["ja_price"]
                mkt_mo  = avg_market * packs
                ja_mo   = jp * packs
                saved_mo = mkt_mo - ja_mo
                saved_yr = saved_mo * 12

                m1, m2, m3 = st.columns(3)
                pct = f"-{saved_mo/mkt_mo*100:.0f}%" if mkt_mo > 0 else ""
                m1.metric("Monthly Savings",  f"₹{saved_mo:,.2f}", delta=pct)
                m2.metric("Yearly Savings",   f"₹{saved_yr:,.2f}")
                m3.metric("10-Year Savings",  f"₹{saved_yr*10:,.2f}")

            fig = go.Figure()
            fig.add_trace(go.Bar(name="Market", x=["Monthly","Yearly","10-Year"],
                y=[mkt_mo, mkt_mo*12, mkt_mo*120], marker_color="#e53935",
                text=[f"₹{mkt_mo:.0f}", f"₹{mkt_mo*12:.0f}", f"₹{mkt_mo*120:.0f}"],
                textposition="outside"))
            fig.add_trace(go.Bar(name="Jan Aushadhi", x=["Monthly","Yearly","10-Year"],
                y=[ja_mo, ja_mo*12, ja_mo*120], marker_color="#2e7d32",
                text=[f"₹{ja_mo:.0f}", f"₹{ja_mo*12:.0f}", f"₹{ja_mo*120:.0f}"],
                textposition="outside"))
            fig.update_layout(title="Market vs Jan Aushadhi Spending",
                yaxis_title="Amount (₹)", barmode="group", height=380, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(
                f'<div class="savings-box">💡 Switching to Jan Aushadhi for '
                f'<b>{result["generic_name"]}</b> ({packs} pack/month) saves '
                f'<b>₹{saved_yr:,.2f}/year</b>. Over 10 years: <b>₹{saved_yr*10:,.2f}</b>.</div>',
                unsafe_allow_html=True)

            st.markdown("---")
            st.info("📌 Switch to the **🧬 Know Your Drug** tab to learn about this medicine's uses, side effects, and more.")


# ── PAGE 2: Know Your Drug ────────────────────────────────────────────────────
elif page == "🧬 Know Your Drug":
    st.markdown("## 🧬 Know Your Drug")
    st.markdown("Get complete information about any medicine — uses, side effects, safety, and Jan Aushadhi alternatives.")

    if 'autocomplete_options' not in st.session_state:
        st.session_state.autocomplete_options = recommender.get_autocomplete_options()

    drug_query = st.selectbox(
        "Search drug",
        options=[""] + st.session_state.autocomplete_options,
        index=0,
        key="drug_search",
        label_visibility="collapsed",
        placeholder="Type any medicine name...",
    )
    st.caption("💡 Works for branded names like 'Augmentin 625' or generic names like 'Amoxicillin'")

    if drug_query:
        # Get Jan Aushadhi result
        ja_result = recommender.get_generic_alternatives(drug_query)

        # Get full drug meta
        key = drug_query.strip().lower()
        meta = recommender.medicine_meta.get(key, {})
        if not meta:
            from rapidfuzz import fuzz, process as fzp
            keys = list(recommender.medicine_meta.keys())
            hit = fzp.extractOne(key, keys, scorer=fuzz.partial_ratio)
            if hit and hit[1] >= 75:
                meta = recommender.medicine_meta[hit[0]]

        if not meta and not ja_result:
            st.warning(f"No information found for '{drug_query}'. Try a different name.")
        else:
            name    = meta.get('name', drug_query) if meta else (ja_result['generic_name'] if ja_result else drug_query)
            tc      = meta.get('therapeutic_class', ja_result['therapeutic_class'] if ja_result else '—')
            uses    = meta.get('uses', [ja_result['indication']] if ja_result else [])
            se      = meta.get('side_effects', [])
            hf      = meta.get('habit_forming', 'No')
            chem    = meta.get('chemical_class', '')
            action  = meta.get('action_class', '')

            composition = ja_result['composition'] if ja_result else '—'
            strength    = ja_result['strength']    if ja_result else '—'
            form        = ja_result['dosage_form'] if ja_result else '—'

            # ── Big medicine card ─────────────────────────────────────────────
            st.markdown(f"---")
            st.markdown(f"# 💊 {name.title()}")

            # Top badges
            badge_html = f'<span class="badge">{tc}</span>'
            if hf and hf.lower() not in ('no','nan',''):
                badge_html += f'<span class="badge-orange">⚠️ Habit Forming: {hf}</span>'
            else:
                badge_html += '<span class="badge">✅ Non Habit Forming</span>'
            st.markdown(badge_html, unsafe_allow_html=True)
            st.markdown("")

            # Key info row
            ki1, ki2, ki3, ki4 = st.columns(4)
            ki1.metric("Composition",    composition[:30] if composition != '—' else '—')
            ki2.metric("Strength",       strength)
            ki3.metric("Dosage Form",    form)
            ki4.metric("Category",       tc[:22])

            st.markdown("")

            # ── TABS ─────────────────────────────────────────────────────────
            t1, t2, t3, t4 = st.tabs(["📋 Uses & Benefits", "⚠️ Side Effects", "🔬 Drug Info", "💰 Jan Aushadhi Price"])

            with t1:
                st.markdown('<p class="drug-section-title">🎯 What is this medicine used for?</p>', unsafe_allow_html=True)
                if uses:
                    for u in uses:
                        st.markdown(f'<span class="pill-use">✔ {u}</span>', unsafe_allow_html=True)
                else:
                    st.info("Use information not available for this medicine.")

                if chem:
                    st.markdown('<p class="drug-section-title" style="margin-top:1.5rem">⚗️ Chemical Class</p>', unsafe_allow_html=True)
                    st.markdown(f"**{chem}**")

                if action:
                    st.markdown('<p class="drug-section-title">⚙️ How It Works (Action Class)</p>', unsafe_allow_html=True)
                    st.markdown(f"{action}")

            with t2:
                st.markdown('<p class="drug-section-title">⚠️ Common Side Effects</p>', unsafe_allow_html=True)
                if se:
                    for s in se:
                        st.markdown(f'<span class="pill-se">• {s}</span>', unsafe_allow_html=True)
                    st.markdown("")
                    st.warning("⚠️ Side effects vary by individual. Always consult your doctor if you experience discomfort.")
                else:
                    st.info("Side effect data not available. Consult your doctor or pharmacist.")

            with t3:
                st.markdown('<p class="drug-section-title">🔬 Technical Details</p>', unsafe_allow_html=True)
                info_data = {
                    "Generic / Salt Name":   composition,
                    "Strength":              strength,
                    "Dosage Form":           form,
                    "Therapeutic Class":     tc,
                    "Chemical Class":        chem or "—",
                    "Action Class":          action or "—",
                    "Habit Forming":         hf,
                }
                info_df = pd.DataFrame(info_data.items(), columns=["Property", "Value"])
                st.dataframe(info_df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown('<p class="drug-section-title">📌 Important Safety Notes</p>', unsafe_allow_html=True)
                st.markdown("""
- Always take this medicine in the dose and duration as advised by your doctor.
- Do not stop taking the medicine without consulting your doctor.
- Keep out of reach of children.
- Store in a cool, dry place away from direct sunlight.
- Check for allergies before starting any new medicine.
                """)

            with t4:
                st.markdown('<p class="drug-section-title">💰 Jan Aushadhi Pricing</p>', unsafe_allow_html=True)
                if ja_result:
                    ja_alts = ja_result["ja_alternatives"]
                    if ja_alts:
                        cheapest = ja_alts[0]
                        p1, p2, p3 = st.columns(3)
                        p1.metric("Jan Aushadhi Price", f"₹{cheapest['ja_price']:.2f}")
                        p2.metric("Market Price",       f"₹{ja_result['branded_price']:.2f}")
                        p3.metric("You Save",           f"{cheapest['savings_pct']:.0f}%")

                        st.markdown("")
                        ja_df = pd.DataFrame([{
                            "Generic Name":  r["name"],
                            "Pack":          r["pack_size"],
                            "JA Price (₹)":  f"₹{r['ja_price']:.2f}",
                            "Savings %":     f"{r['savings_pct']:.0f}%",
                            "JA Code":       r["ja_code"],
                        } for r in ja_alts])

                        def hl2(row):
                            return ['background-color:#c8e6c9;color:#1b5e20']*len(row) if row.name==0 else ['']*len(row)
                        st.dataframe(ja_df.style.apply(hl2, axis=1),
                                     use_container_width=True, hide_index=True)
                    else:
                        st.info("No Jan Aushadhi price listed. Ask at your nearest Kendra.")
                else:
                    st.info("Search the medicine in 'Find Generic Alternative' tab for price data.")

                st.markdown("---")
                st.info("📍 Use the **Nearest Jan Aushadhi Store** tab to find where to buy.")


# ── PAGE 3: Nearest Store ─────────────────────────────────────────────────────
elif page == "📍 Nearest Jan Aushadhi Store":
    st.markdown("## 📍 Find Your Nearest Jan Aushadhi Store")
    st.markdown("Pradhan Mantri Bhartiya Janaushadhi Kendras sell generic medicines at up to 90% discount.")

    search_method = st.radio("Search by", ["By Pincode", "By City", "By State", "By Coordinates"], horizontal=True)

    nearest_stores = []
    center_lat, center_lon = 20.5937, 78.9629

    if search_method == "By Pincode":
        pin = st.text_input("Enter your 6-digit pincode", placeholder="e.g. 141001")
        if pin and len(pin) == 6 and pin.isdigit():
            coords = pincode_to_coords(pin)
            if coords:
                center_lat, center_lon = coords
                nearest_stores = locator.find_nearest(center_lat, center_lon, n=5)
                st.success(f"Showing stores near pincode {pin}")
            else:
                matches = locator.find_by_pincode(pin)
                if matches:
                    nearest_stores = matches
                    center_lat = matches[0]["latitude"]
                    center_lon = matches[0]["longitude"]
                    st.success(f"Found {len(matches)} store(s) in pincode {pin}")
                else:
                    st.warning("No stores found. Try nearby pincode or city search.")

    elif search_method == "By State":
        state = st.selectbox("Select state", [""] + locator.get_all_states())
        if state:
            nearest_stores = locator.find_by_state(state)
            if nearest_stores:
                center_lat = nearest_stores[0]["latitude"]
                center_lon = nearest_stores[0]["longitude"]

    elif search_method == "By City":
        city = st.selectbox("Select your city", [""] + locator.get_all_cities())
        if city:
            nearest_stores = locator.find_by_city(city)
            if nearest_stores:
                center_lat = nearest_stores[0]["latitude"]
                center_lon = nearest_stores[0]["longitude"]

    else:
        lc1, lc2 = st.columns(2)
        with lc1: user_lat = st.number_input("Latitude",  value=30.9010, format="%.4f")
        with lc2: user_lon = st.number_input("Longitude", value=75.8573, format="%.4f")
        if st.button("Find nearest stores"):
            nearest_stores = locator.find_nearest(user_lat, user_lon, n=5)
            center_lat, center_lon = user_lat, user_lon

    if nearest_stores:
        st.markdown(f"### Found {len(nearest_stores)} store(s)")
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11)
        for store in nearest_stores:
            popup_html = f"<b>{store['store_name']}</b><br>{store['address']}<br>📞 {store['phone']}<br>🕐 {store['operating_hours']}"
            folium.Marker(
                [store["latitude"], store["longitude"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=store["store_name"],
                icon=folium.Icon(color="green", icon="plus", prefix="fa"),
            ).add_to(m)
        st_folium(m, height=450, use_container_width=True)

        for i, store in enumerate(nearest_stores, 1):
            with st.expander(f"{i}. {store['store_name']}" + (f"  —  {store.get('distance_km','N/A')} km" if 'distance_km' in store else "")):
                ec1, ec2 = st.columns(2)
                ec1.markdown(f"**Address:** {store['address']}, {store['city']}  \n**State:** {store['state']}  \n**Pincode:** {store['pincode']}")
                ec2.markdown(f"**Phone:** {store['phone']}  \n**Hours:** {store['operating_hours']}  \n[🗺️ Get Directions]({locator.get_directions_url(store['latitude'], store['longitude'])})")


# ── PAGE 4: Browse by Category ────────────────────────────────────────────────
elif page == "📊 Browse by Category":
    st.markdown("## 📊 Browse Medicines by Category")
    st.markdown("Explore the Jan Aushadhi database by therapeutic class.")

    category = st.selectbox("Therapeutic class", recommender.get_all_classes())
    if category:
        meds = recommender.get_by_therapeutic_class(category)
        st.caption(f"Found {len(meds)} medicines in this category")
        display_df = pd.DataFrame(meds)[["generic_name","strength","generic_price","pack_size"]].copy()
        display_df.columns = ["Generic Name","Strength","Jan Aushadhi Price (₹)","Pack Size"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        avg = display_df["Jan Aushadhi Price (₹)"].mean()
        st.info(f"💰 Average Jan Aushadhi price in this category: **₹{avg:.2f}**")


# ── PAGE 5: Savings Calculator ────────────────────────────────────────────────
elif page == "💰 Savings Calculator":
    st.markdown("## 💰 Household Savings Calculator")
    st.markdown("Add the medicines your family uses regularly. See how much you save by switching to Jan Aushadhi.")

    if "cart" not in st.session_state:
        st.session_state.cart = []

    cc1, cc2, cc3 = st.columns([3, 1, 1])
    with cc1:
        med = st.selectbox("Medicine", [""] + recommender.df["generic_name"].unique().tolist(), key="med_select")
    with cc2:
        packs = st.number_input("Packs/month", min_value=1, max_value=30, value=2)
    with cc3:
        st.write(""); st.write("")
        if st.button("Add ➕", use_container_width=True) and med:
            match = recommender.df[recommender.df["generic_name"] == med].iloc[0]
            st.session_state.cart.append({
                "generic": med, "packs": packs,
                "monthly_market": float(match["branded_price"]) * packs,
                "monthly_ja":     float(match["generic_price"])  * packs,
            })

    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        disp = cart_df[["generic","packs","monthly_market","monthly_ja"]].copy()
        disp["savings"] = disp["monthly_market"] - disp["monthly_ja"]
        disp.columns = ["Generic Name","Packs/mo","Market ₹/mo","JA ₹/mo","Savings ₹/mo"]
        st.dataframe(disp, use_container_width=True, hide_index=True)

        tm = cart_df["monthly_market"].sum()
        tj = cart_df["monthly_ja"].sum()
        ms = tm - tj

        m1, m2, m3 = st.columns(3)
        m1.metric("Market/month",    f"₹{tm:,.2f}")
        m2.metric("Jan Aushadhi/mo", f"₹{tj:,.2f}", delta=f"-₹{ms:,.2f}")
        m3.metric("Yearly Savings",  f"₹{ms*12:,.2f}")

        st.markdown(f'<div class="savings-box">🎯 Your family saves <b>₹{ms*12:,.2f}/year</b> with Jan Aushadhi. Over 30 years: <b>₹{ms*12*30:,.2f}</b>.</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear list"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("Add medicines above to start calculating.")


# ── PAGE 6: About ─────────────────────────────────────────────────────────────
else:
    st.markdown("## ℹ️ About This Project")
    st.markdown("""
### The Problem
Indians spend over **₹1.8 lakh crore** on medicines every year. Branded medicines often cost **5–10× more** than their generic equivalents — same molecule, same efficacy, drastically different price.

The Government of India's **PMBJP scheme** operates over **14,000 Jan Aushadhi Kendras** selling quality-tested generics at 50–90% lower prices. But awareness remains critically low — less than 15% of households use it.

### What This Tool Does
- **Find** the Jan Aushadhi generic for any branded medicine
- **Know Your Drug** — full information: uses, side effects, chemical class, action class
- **Compare** prices and project 10-year household savings
- **Locate** the nearest Jan Aushadhi Kendra

### Tech Stack
Python · Streamlit · Pandas · RapidFuzz · Plotly · Folium

### Data Sources
- PMBJP official product list (janaushadhi.gov.in)
- Medicine dataset with 248K medicines, uses, side effects
- Curated Jan Aushadhi Kendra locations

### Disclaimer
⚠️ Informational tool only. Always consult your doctor before switching medicines.
    """)
