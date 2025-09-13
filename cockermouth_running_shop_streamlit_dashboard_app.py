# Cockermouth Running Shop – Lightweight Web Dashboard (Streamlit)
# ---------------------------------------------------------------
# Free to run on https://streamlit.io/cloud or locally.
# Requirements (add these to requirements.txt when deploying):
#   streamlit>=1.32
#   pandas>=2.0
#   numpy>=1.24
#   matplotlib>=3.7
# ---------------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Running Shop Model – Cockermouth", layout="wide")
st.title("🏃 Cockermouth Running Shop – Tweakable Model")
st.caption("Locals-first revenue & P&L model with seasonality and presets. ")

# -------- Helpers --------
def fmt_gbp(x):
    try:
        return f"£{x:,.0f}"
    except Exception:
        return "—"

# Defaults (aligned with our earlier discussion)
defaults = dict(
    pop=8860,
    adult_share=0.80,
    run_share=0.30,
    pairs_per_runner=0.70,
    capture_local=0.40,
    asp_shoes=130.0,
    attach_apparel=0.40,
    tourist_footfall=8000,
    tourist_conv=0.020,
    tourist_aov=125.0,
    num_events=2,
    event_sales=6000.0,
    service_units=400,
    service_price=10.0,
    gm_shoes=0.43,
    gm_apparel=0.52,
    gm_tour=0.45,
    rent=29000.0,
    staff=15000.0,
    utilities=7000.0,
    marketing=8000.0,
    misc=5000.0,
    other=0.0,
    summer_uplift=0.25,
    shoulder_uplift=0.10,
)

presets = {
    "Conservative": {**defaults, **dict(
        capture_local=0.30,
        tourist_footfall=6000,
        tourist_conv=0.015,
        num_events=1,
        event_sales=5000.0,
        staff=12000.0,
        marketing=6000.0,
    )},
    "Base": defaults,
    "Stretch": {**defaults, **dict(
        capture_local=0.55,
        tourist_footfall=10000,
        tourist_conv=0.025,
        num_events=3,
        event_sales=8000.0,
        staff=20000.0,
        marketing=10000.0,
    )},
}

# -------- Sidebar controls --------
with st.sidebar:
    st.header("⚙️ Controls")
    preset_name = st.radio("Preset", list(presets.keys()), index=1, horizontal=True)
    p = presets[preset_name]

    st.subheader("Local demand")
    pop = st.number_input("Local population", min_value=1000, value=int(p["pop"]))
    adult_share = st.slider("Adults (% of population)", 0.50, 0.95, float(p["adult_share"]))
    run_share = st.slider("Run at least occasionally (% of adults)", 0.05, 0.60, float(p["run_share"]))
    pairs_per_runner = st.slider("Pairs per runner / year", 0.20, 2.0, float(p["pairs_per_runner"]))
    capture_local = st.slider("Your capture of local pairs", 0.05, 0.90, float(p["capture_local"]))
    asp_shoes = st.number_input("Average shoe price (ASP, £)", min_value=40.0, value=float(p["asp_shoes"]))
    attach_apparel = st.slider("Apparel+accessories as % of shoe revenue", 0.0, 1.0, float(p["attach_apparel"]))

    st.subheader("Tourism & events")
    tourist_footfall = st.number_input("Reachable tourist footfall / year", min_value=0, value=int(p["tourist_footfall"]))
    tourist_conv = st.slider("Tourist conversion rate", 0.0, 0.10, float(p["tourist_conv"]))
    tourist_aov = st.number_input("Tourist average order value (£)", min_value=10.0, value=float(p["tourist_aov"]))
    num_events = st.number_input("Major event weeks / year", min_value=0, value=int(p["num_events"]))
    event_sales = st.number_input("Avg sales per event week (£)", min_value=0.0, value=float(p["event_sales"]))

    st.subheader("Service revenue (gait / fitting)")
    service_units = st.number_input("Chargeable services / year", min_value=0, value=int(p["service_units"]))
    service_price = st.number_input("Average service price (£)", min_value=0.0, value=float(p["service_price"]))

    st.subheader("Margins (gross)")
    gm_shoes = st.slider("Shoes GM%", 0.20, 0.60, float(p["gm_shoes"]))
    gm_apparel = st.slider("Apparel/acc. GM%", 0.30, 0.70, float(p["gm_apparel"]))
    gm_tour = st.slider("Tourist basket GM%", 0.20, 0.60, float(p["gm_tour"]))

    st.subheader("Operating costs (annual)")
    rent = st.number_input("Rent & rates (£)", min_value=0.0, value=float(p["rent"]))
    staff = st.number_input("Staff (£)", min_value=0.0, value=float(p["staff"]))
    utilities = st.number_input("Utilities/insurance/EPOS (£)", min_value=0.0, value=float(p["utilities"]))
    marketing = st.number_input("Marketing & events (£)", min_value=0.0, value=float(p["marketing"]))
    misc = st.number_input("Misc. & professional fees (£)", min_value=0.0, value=float(p["misc"]))
    other = st.number_input("Other opex (£)", min_value=0.0, value=float(p["other"]))

    st.subheader("Seasonality (uplift vs base)")
    summer_uplift = st.slider("June–Aug uplift", 0.0, 0.75, float(p["summer_uplift"]))
    shoulder_uplift = st.slider("May & Sep uplift", 0.0, 0.50, float(p["shoulder_uplift"]))

# -------- Core calculations --------
adults = pop * adult_share
runners = adults * run_share
local_pairs = runners * pairs_per_runner
local_pairs_captured = local_pairs * capture_local
rev_local_shoes = local_pairs_captured * asp_shoes
rev_local_apparel = rev_local_shoes * attach_apparel
rev_tourist_core = tourist_footfall * tourist_conv * tourist_aov
rev_events = num_events * event_sales
rev_services = service_units * service_price

turnover = rev_local_shoes + rev_local_apparel + rev_tourist_core + rev_events + rev_services

# Gross profit
gp_shoes = rev_local_shoes * gm_shoes
gp_apparel = rev_local_apparel * gm_apparel
gp_tour = (rev_tourist_core + rev_events) * gm_tour
gp_services = rev_services # assume labour is counted in staff

gp_total = gp_shoes + gp_apparel + gp_tour + gp_services

# Opex & profit
opex = rent + staff + utilities + marketing + misc + other
op = gp_total - opex

# Blended GP%
try:
    gp_pct = gp_total / turnover if turnover > 0 else np.nan
except Exception:
    gp_pct = np.nan

be_sales = (opex / gp_pct) if (gp_pct and gp_pct > 0) else np.nan

# -------- Layout: KPIs --------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Turnover", fmt_gbp(turnover))
col2.metric("Gross profit", fmt_gbp(gp_total), None)
col3.metric("Opex", fmt_gbp(opex), None)
col4.metric("Operating profit", fmt_gbp(op), None)

st.caption(f"Blended GP%: {gp_pct*100:.1f}% | Breakeven sales: {fmt_gbp(be_sales) if not np.isnan(be_sales) else '—'}")

# -------- Charts --------
st.subheader("Revenue breakdown")
rev_df = pd.DataFrame({
    "Stream": ["Local shoes", "Local apparel/acc.", "Tourist core", "Event bursts", "Services"],
    "Revenue": [rev_local_shoes, rev_local_apparel, rev_tourist_core, rev_events, rev_services],
})
fig1, ax1 = plt.subplots()
ax1.bar(rev_df["Stream"], rev_df["Revenue"])  # No explicit colours per instructions
ax1.set_ylabel("Revenue (annual)")
ax1.set_xlabel("")
ax1.set_title("Revenue by stream")
ax1.tick_params(axis='x', rotation=15)
for i, v in enumerate(rev_df["Revenue"]):
    ax1.text(i, v, fmt_gbp(v), ha='center', va='bottom')
st.pyplot(fig1)

st.subheader("Seasonality – monthly turnover profile")
base = np.ones(12)
upl = base.copy()
upl[[4, 8]] *= (1 + shoulder_uplift)   # May (index 4), Sep (index 8)
upl[5:8] *= (1 + summer_uplift)         # Jun–Aug (index 5:7)
shares = upl / upl.sum()
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
season_df = pd.DataFrame({"Month": months, "Turnover": shares * turnover})
fig2, ax2 = plt.subplots()
ax2.plot(season_df["Month"], season_df["Turnover"])  # No explicit colours
ax2.scatter(season_df["Month"], season_df["Turnover"])
for i, v in enumerate(season_df["Turnover"]):
    ax2.text(i, v, fmt_gbp(v), ha='center', va='bottom')
ax2.set_ylabel("Turnover per month")
ax2.set_xlabel("")
ax2.set_title("Seasonality profile (derived from annual turnover)")
st.pyplot(fig2)

# -------- Detailed table --------
st.subheader("Detailed metrics")
summary = pd.DataFrame({
    "Metric": [
        "Adults","Runners","Local pairs (all)","Local pairs captured",
        "Local shoe revenue","Local apparel/acc. revenue",
        "Tourist revenue (core)","Event burst revenue","Service revenue",
        "TOTAL turnover","GP – shoes","GP – apparel/acc.","GP – tourist/events","GP – services",
        "TOTAL gross profit","Opex","Operating profit","Blended GP%","Breakeven sales"
    ],
    "Value": [
        round(adults), round(runners), round(local_pairs), round(local_pairs_captured),
        fmt_gbp(rev_local_shoes), fmt_gbp(rev_local_apparel), fmt_gbp(rev_tourist_core), fmt_gbp(rev_events), fmt_gbp(rev_services),
        fmt_gbp(turnover), fmt_gbp(gp_shoes), fmt_gbp(gp_apparel), fmt_gbp(gp_tour), fmt_gbp(gp_services),
        fmt_gbp(gp_total), fmt_gbp(opex), fmt_gbp(op),
        f"{gp_pct*100:.1f}%" if not np.isnan(gp_pct) else "—",
        fmt_gbp(be_sales) if not np.isnan(be_sales) else "—",
    ]
})
st.dataframe(summary, use_container_width=True, hide_index=True)

# -------- Download CSV --------
assumptions_outputs = {
    "Population": pop,
    "Adult share": adult_share,
    "Runner share": run_share,
    "Pairs per runner": pairs_per_runner,
    "Capture local": capture_local,
    "ASP shoes": asp_shoes,
    "Attach apparel": attach_apparel,
    "Tourist footfall": tourist_footfall,
    "Tourist conversion": tourist_conv,
    "Tourist AOV": tourist_aov,
    "Event weeks": num_events,
    "Event sales per week": event_sales,
    "Service units": service_units,
    "Service price": service_price,
    "GM shoes": gm_shoes,
    "GM apparel": gm_apparel,
    "GM tourist": gm_tour,
    "Rent": rent,
    "Staff": staff,
    "Utilities": utilities,
    "Marketing": marketing,
    "Misc": misc,
    "Other": other,
    "Summer uplift": summer_uplift,
    "Shoulder uplift": shoulder_uplift,
    "Turnover": turnover,
    "Gross profit": gp_total,
    "Opex": opex,
    "Operating profit": op,
    "Breakeven sales": be_sales,
    "Blended GP%": gp_pct,
}
df_download = pd.DataFrame(list(assumptions_outputs.items()), columns=["key","value"]).astype({"key":"string"})
csv_bytes = df_download.to_csv(index=False).encode("utf-8")
st.download_button("Download assumptions & outputs (CSV)", data=csv_bytes, file_name="cockermouth_running_shop_model.csv", mime="text/csv")

st.markdown("""
---
**How to deploy for free:**
1. Create a new repo with this `app.py` and a `requirements.txt` containing:\
   `streamlit\npandas\nnumpy\nmatplotlib`  
2. Go to **Streamlit Community Cloud** → **New app** → select the repo and branch → Deploy.  
3. Share your app URL.

**Notes:** Service GP assumed ~100% (labour is in Staff). Seasonality is a simple uplift model; adjust logic if you want event-specific months.
""")
