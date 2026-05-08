import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Real Estate Conversion Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"]  { font-family: 'DM Sans', sans-serif; }
h1, h2, h3                  { font-family: 'Playfair Display', serif !important; }
.main                       { background-color: #f7f5f0; }
.block-container            { padding: 1.8rem 2.2rem; }

.kpi-card {
    background: white;
    border-radius: 14px;
    padding: 1.3rem 1rem;
    box-shadow: 0 2px 14px rgba(0,0,0,0.07);
    border-left: 5px solid #c8973a;
    margin-bottom: 1rem;
}
.kpi-label       { color:#999; font-size:.72rem; text-transform:uppercase; letter-spacing:1.2px; }
.kpi-value       { color:#1a1a1a; font-size:1.85rem; font-weight:700; font-family:'Playfair Display',serif; line-height:1.1; }
.kpi-delta-green { font-size:.8rem; color:#3d9970; font-weight:500; margin-top:4px; }
.kpi-delta-red   { font-size:.8rem; color:#e74c3c; font-weight:500; margin-top:4px; }

.section-title {
    font-family:'Playfair Display',serif;
    font-size:1.1rem;
    color:#1a1a1a;
    border-bottom:2px solid #c8973a;
    padding-bottom:.3rem;
    margin-bottom:.5rem;
}
.banner {
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
    border-radius:14px;
    padding:1.6rem 2.2rem;
    margin-bottom:1.8rem;
}
.banner h1 { color:#c8973a !important; margin:0; font-size:1.8rem; }
.banner p  { color:#ccc; margin:.3rem 0 0; font-size:.88rem; }

.insight-box {
    background:#fffaf2;
    border-left:4px solid #c8973a;
    border-radius:8px;
    padding:.75rem 1rem;
    font-size:.83rem;
    color:#555;
    margin-top:.4rem;
}
</style>
""", unsafe_allow_html=True)

# ── LOAD & ENRICH DATA ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(
        "real_estate_300.csv",
        parse_dates=["listing_date", "visit_date", "booking_date"],
    )
    df["list_month"]    = df["listing_date"].dt.strftime("%b")
    df["visit_month"]   = df["visit_date"].dt.strftime("%b")
    df["book_month"]    = df["booking_date"].dt.strftime("%b")
    df["days_to_close"] = (df["booking_date"] - df["listing_date"]).dt.days
    df["converted"]     = df["move_in_status"].str.strip().str.lower() == "yes"
    df["price_lakh"]    = (df["price"] / 1e5).round(2)
    return df

df = load_data()

MONTH_ORDER = ["Jan", "Feb", "Mar"]
CITY_COLORS = {
    "Mumbai":    "#0f3460",
    "Pune":      "#c8973a",
    "Hyderabad": "#3d9970",
    "Bangalore": "#e74c3c",
    "Chennai":   "#9b59b6",
}

# ── SUPPLEMENTARY AGENT DATA ──────────────────────────────────────────────────
np.random.seed(42)
_agents = ["Priya S.", "Karan M.", "Divya R.", "Arjun T.", "Sneha K.",
           "Raj P.",   "Meena L.", "Vikram N.", "Pooja A.", "Arun B."]
agent_df = pd.DataFrame({
    "Agent":         _agents,
    "Leads":         np.random.randint(25, 80, 10),
    "Closures":      np.random.randint(8,  35, 10),
    "Revenue_Lakh":  np.random.randint(40, 200, 10),
})
agent_df["Conv_Pct"] = (agent_df["Closures"] / agent_df["Leads"] * 100).round(1)

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    all_cities = sorted(df["city"].unique().tolist())
    sel_cities = st.multiselect("City / Region", all_cities, default=all_cities)

    all_types  = sorted(df["property_type"].unique().tolist())
    sel_types  = st.multiselect("Property Type", all_types, default=all_types)

    sel_months = st.multiselect("Listing Month", MONTH_ORDER, default=MONTH_ORDER)

    st.markdown("---")
    st.markdown("**Dataset:** `real_estate_300.csv`")

fdf = df[
    df["city"].isin(sel_cities) &
    df["property_type"].isin(sel_types) &
    df["list_month"].isin(sel_months)
].copy()

# ── BANNER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="banner">
  <h1>🏠 Real Estate Conversion Dashboard</h1>
  <p>Dataset: real_estate_300.csv</p>
</div>
""", unsafe_allow_html=True)

# ── KPI METRICS ───────────────────────────────────────────────────────────────
total_listings  = len(fdf)
# visits: every property has a visit_date in this dataset (all 300 visited)
total_visits    = int(fdf["visit_date"].notna().sum())
# bookings: rows with a booking_date (i.e. booking was made = 181)
total_bookings  = int(fdf["booking_date"].notna().sum())
# moved in = converted = Yes in move_in_status
total_moved_in  = int(fdf["converted"].sum())
conv_rate       = round(total_moved_in / total_listings * 100, 1) if total_listings else 0
# Revenue = sum of prices of converted properties only
revenue_cr      = round(fdf[fdf["converted"]]["price"].sum() / 1e7, 2)
avg_days        = round(fdf["days_to_close"].mean(), 1)

def kpi_card(col, label, value, note, red=False):
    cls = "kpi-delta-red" if red else "kpi-delta-green"
    arrow = "▼" if red else "▲"
    col.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="{cls}">{arrow} {note}</div>
    </div>""", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
kpi_card(c1, "Total Listings",      str(total_listings),     "Properties in dataset")
kpi_card(c2, "Site Visits Done",    str(total_visits),       f"{round(total_visits/total_listings*100,1)}% of listings")
kpi_card(c3, "Bookings Made",       str(total_bookings),     f"{round(total_bookings/total_listings*100,1)}% of listings")
kpi_card(c4, "Moved In",            str(total_moved_in),     f"{conv_rate}% conversion rate")
kpi_card(c5, "Revenue (Converted)", f"Rs {revenue_cr} Cr",  "Sold properties only")
kpi_card(c6, "Avg Days to Close",   f"{avg_days} days",      "Listing to move-in", red=avg_days > 20)

st.markdown("---")

# ── ROW 1 · FUNNEL  +  CITY CONVERSIONS ──────────────────────────────────────
r1c1, r1c2 = st.columns([1.1, 1])

with r1c1:
    st.markdown('<div class="section-title">📊 Home Seeker Conversion Funnel</div>',
                unsafe_allow_html=True)
    fig_f = go.Figure(go.Funnel(
        y=["Listed / Enquired", "Site Visit Done", "Booking Made", "Moved In"],
        x=[total_listings, total_visits, total_bookings, total_moved_in],
        textinfo="value+percent initial",
        marker=dict(color=["#0f3460", "#1a4a7a", "#c8973a", "#3d9970"]),
        connector=dict(line=dict(color="#e0e0e0", width=1)),
    ))
    fig_f.update_layout(height=340, paper_bgcolor="white",
                        margin=dict(l=10,r=10,t=15,b=10),
                        font=dict(family="DM Sans"))
    st.plotly_chart(fig_f, use_container_width=True)
    st.markdown(
        f'<div class="insight-box">💡 Out of <b>{total_listings}</b> listings, '
        f'<b>{total_bookings}</b> were booked and <b>{total_moved_in}</b> '
        f'successfully moved in — a <b>{conv_rate}%</b> conversion rate.</div>',
        unsafe_allow_html=True,
    )

with r1c2:
    st.markdown('<div class="section-title">📍 Move-In Conversions by City</div>',
                unsafe_allow_html=True)
    city_grp = fdf.groupby("city").agg(
        Total    = ("property_id", "count"),
        Moved_In = ("converted",   "sum"),
    ).reset_index()
    city_grp["Not_Moved"] = city_grp["Total"] - city_grp["Moved_In"]
    city_grp["Rate"]      = (city_grp["Moved_In"] / city_grp["Total"] * 100).round(1)

    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(name="Moved In",     x=city_grp["city"],
                           y=city_grp["Moved_In"],  marker_color="#3d9970"))
    fig_c.add_trace(go.Bar(name="Not Moved In", x=city_grp["city"],
                           y=city_grp["Not_Moved"], marker_color="#d0d0d0"))
    fig_c.update_layout(
        barmode="stack", height=340, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
        legend=dict(orientation="h", y=-0.22),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_c, use_container_width=True)
    if not city_grp.empty:
        bc = city_grp.loc[city_grp["Rate"].idxmax()]
        st.markdown(
            f'<div class="insight-box">💡 <b>{bc["city"]}</b> leads with the '
            f'highest conversion rate at <b>{bc["Rate"]}%</b>.</div>',
            unsafe_allow_html=True,
        )

# ── ROW 2 · MONTHLY TREND  +  REVENUE BY CITY ────────────────────────────────
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.markdown('<div class="section-title">📅 Monthly Listing → Visit → Booking → Move-In</div>',
                unsafe_allow_html=True)
    m_list  = fdf.groupby("list_month").size().reindex(MONTH_ORDER, fill_value=0)
    m_visit = fdf.groupby("visit_month").size().reindex(MONTH_ORDER, fill_value=0)
    m_book  = (fdf[fdf["book_month"].notna()]
               .groupby("book_month").size()
               .reindex(MONTH_ORDER, fill_value=0))
    m_moved = (fdf[fdf["converted"]]
               .groupby("list_month").size()
               .reindex(MONTH_ORDER, fill_value=0))

    fig_t = go.Figure()
    fig_t.add_trace(go.Bar(name="Listings", x=MONTH_ORDER, y=m_list.values,  marker_color="#0f3460"))
    fig_t.add_trace(go.Bar(name="Visits",   x=MONTH_ORDER, y=m_visit.values, marker_color="#c8973a"))
    fig_t.add_trace(go.Bar(name="Bookings", x=MONTH_ORDER, y=m_book.values,  marker_color="#3d9970"))
    fig_t.add_trace(go.Bar(name="Moved In", x=MONTH_ORDER, y=m_moved.values, marker_color="#e74c3c"))
    fig_t.update_layout(
        barmode="group", height=320, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
        legend=dict(orientation="h", y=-0.28),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_t, use_container_width=True)

with r2c2:
    st.markdown('<div class="section-title">💰 Monthly Revenue — Converted Properties (Rs Lakh)</div>',
                unsafe_allow_html=True)
    rev_src = fdf[fdf["converted"]].copy()
    rev_src["Month"] = rev_src["listing_date"].dt.strftime("%b")
    rcm = (rev_src.groupby(["Month", "city"])["price_lakh"]
           .sum().reset_index()
           .query("Month in @MONTH_ORDER"))

    fig_r = go.Figure()
    for city in sel_cities:
        d = rcm[rcm["city"] == city]
        fig_r.add_trace(go.Bar(
            name=city, x=d["Month"], y=d["price_lakh"],
            marker_color=CITY_COLORS.get(city, "#888"),
        ))
    fig_r.update_layout(
        barmode="stack", height=320, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
        legend=dict(orientation="h", y=-0.28),
        yaxis=dict(gridcolor="#f0f0f0", title="Rs Lakh"),
    )
    st.plotly_chart(fig_r, use_container_width=True)

# ── ROW 3 · PROPERTY TYPE  +  PRICE BOX PLOT ─────────────────────────────────
r3c1, r3c2 = st.columns(2)

with r3c1:
    st.markdown('<div class="section-title">🏘️ Property Type: Listed vs Moved In</div>',
                unsafe_allow_html=True)
    pt = fdf.groupby("property_type").agg(
        Listed   = ("property_id", "count"),
        Moved_In = ("converted",   "sum"),
    ).reset_index()
    pt["Rate"] = (pt["Moved_In"] / pt["Listed"] * 100).round(1)

    fig_p = go.Figure()
    fig_p.add_trace(go.Bar(name="Listed",   x=pt["property_type"], y=pt["Listed"],
                           marker_color="#0f3460"))
    fig_p.add_trace(go.Bar(name="Moved In", x=pt["property_type"], y=pt["Moved_In"],
                           marker_color="#c8973a"))
    fig_p.update_layout(
        barmode="group", height=310, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
        legend=dict(orientation="h", y=-0.28),
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig_p, use_container_width=True)
    if not pt.empty:
        bp = pt.loc[pt["Rate"].idxmax()]
        st.markdown(
            f'<div class="insight-box">💡 <b>{bp["property_type"]}</b> has the best '
            f'conversion rate at <b>{bp["Rate"]}%</b>.</div>',
            unsafe_allow_html=True,
        )

with r3c2:
    st.markdown('<div class="section-title">💵 Price Distribution by Property Type (Rs Lakh)</div>',
                unsafe_allow_html=True)
    BOX_COLORS = {"Apartment": "#0f3460", "Villa": "#c8973a", "Studio": "#3d9970"}
    fig_b = go.Figure()
    for pt_name in sel_types:
        sub = fdf[fdf["property_type"] == pt_name]["price_lakh"]
        fig_b.add_trace(go.Box(
            y=sub, name=pt_name,
            marker_color=BOX_COLORS.get(pt_name, "#888"),
            boxmean=True, line_width=2,
        ))
    fig_b.update_layout(
        height=310, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
        yaxis=dict(gridcolor="#f0f0f0", title="Price (Rs Lakh)"),
        showlegend=False,
    )
    st.plotly_chart(fig_b, use_container_width=True)

# ── ROW 4 · REVENUE PIE  +  HEATMAP ──────────────────────────────────────────
r4c1, r4c2 = st.columns(2)

with r4c1:
    st.markdown('<div class="section-title">📊 Revenue Share by City — Converted Properties</div>',
                unsafe_allow_html=True)
    rev_city = (fdf[fdf["converted"]]
                .groupby("city")["price_lakh"]
                .sum().reset_index()
                .rename(columns={"city": "City", "price_lakh": "Revenue_Lakh"}))

    fig_pie = px.pie(
        rev_city, names="City", values="Revenue_Lakh",
        color="City", color_discrete_map=CITY_COLORS,
        hole=0.42,
    )
    fig_pie.update_traces(
        textinfo="label+percent",
        pull=[0.04] * len(rev_city),
        textfont_size=12,
    )
    fig_pie.update_layout(
        height=340, paper_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
        legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
        font=dict(family="DM Sans"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with r4c2:
    st.markdown('<div class="section-title">⏱️ Avg Days to Close — City × Property Type</div>',
                unsafe_allow_html=True)
    close_df = (fdf[fdf["days_to_close"].notna()]
                .groupby(["city", "property_type"])["days_to_close"]
                .mean().round(1).reset_index())
    if not close_df.empty:
        piv = close_df.pivot(index="city", columns="property_type",
                             values="days_to_close").fillna(0)
        fig_h = go.Figure(go.Heatmap(
            z=piv.values,
            x=piv.columns.tolist(),
            y=piv.index.tolist(),
            colorscale=[[0, "#d4efdf"], [0.5, "#f0c060"], [1, "#0f3460"]],
            text=piv.values.round(1),
            texttemplate="%{text} days",
            showscale=True,
        ))
        fig_h.update_layout(
            height=340, paper_bgcolor="white",
            margin=dict(l=10,r=10,t=15,b=10), font=dict(family="DM Sans"),
            xaxis_title="Property Type", yaxis_title="City",
        )
        st.plotly_chart(fig_h, use_container_width=True)

# ── ROW 5 · CONVERSION RATE GAUGE PER CITY ───────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">🎯 Conversion Rate Gauge — by City</div>',
            unsafe_allow_html=True)

city_rates = (fdf.groupby("city")
              .apply(lambda g: round(g["converted"].sum() / len(g) * 100, 1))
              .reset_index()
              .rename(columns={0: "Rate"}))

gauge_cols = st.columns(len(city_rates))
for i, row in city_rates.iterrows():
    with gauge_cols[i]:
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row["Rate"],
            number={"suffix": "%", "font": {"size": 22, "family": "Playfair Display"}},
            title={"text": row["city"], "font": {"size": 13, "family": "DM Sans"}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"size": 9}},
                "bar":  {"color": CITY_COLORS.get(row["city"], "#888")},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 40],  "color": "#f8f8f8"},
                    {"range": [40, 70], "color": "#fff8ee"},
                    {"range": [70, 100],"color": "#eafaf1"},
                ],
                "threshold": {
                    "line": {"color": "#c8973a", "width": 3},
                    "thickness": 0.75,
                    "value": 60,
                },
            },
        ))
        fig_g.update_layout(
            height=200, paper_bgcolor="white",
            margin=dict(l=15, r=15, t=30, b=10),
            font=dict(family="DM Sans"),
        )
        st.plotly_chart(fig_g, use_container_width=True)

# ── ROW 6 · AGENT LEADERBOARD ─────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">🏆 Agent Performance Leaderboard (Supplementary)</div>',
            unsafe_allow_html=True)
st.caption("Agent data is illustrative — not present in real_estate_300.csv")

agent_show = agent_df.sort_values("Closures", ascending=False).reset_index(drop=True).copy()
agent_show.index += 1

# FIX: use plain ASCII column names to avoid format string encoding issues
agent_show = agent_show.rename(columns={
    "Agent":        "Agent",
    "Leads":        "Leads Assigned",
    "Closures":     "Closures",
    "Revenue_Lakh": "Revenue (Lakh)",
    "Conv_Pct":     "Conversion %",
})

# FIX: use st.dataframe with plain formatting — no special Unicode in format dict
st.dataframe(
    agent_show.style
        .background_gradient(subset=["Closures"],      cmap="YlOrBr")
        .background_gradient(subset=["Conversion %"],  cmap="Greens")
        .format({
            "Revenue (Lakh)": "Rs {:,.0f}",
            "Conversion %":   "{:.1f}%",
        }),
    use_container_width=True,
    height=390,
)