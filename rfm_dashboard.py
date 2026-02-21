import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="Executive Customer Segmentation",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Executive Customer Segmentation Dashboard")
st.markdown("""
### RFM-Based Behavioral Analytics | Production-Style Interactive Dashboard

This dashboard applies **RFM (Recency, Frequency, Monetary) Analysis**
to identify high-value customers, retention risk, and revenue drivers.
""")

# ------------------------------------------------
# LOAD DATA
# ------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Superstore.csv", encoding="latin1")
    return df

df = load_data()
df['Order Date'] = pd.to_datetime(df['Order Date'])

# ------------------------------------------------
# BUILD RFM
# ------------------------------------------------
snapshot_date = df['Order Date'].max() + pd.Timedelta(days=1)

rfm = df.groupby('Customer ID').agg({
    'Order Date': lambda x: (snapshot_date - x.max()).days,
    'Customer ID': 'count',
    'Sales': 'sum'
}).rename(columns={
    'Order Date': 'Recency',
    'Customer ID': 'Frequency',
    'Sales': 'Monetary'
})

# Score customers (5 = best)
rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1,2,3,4,5])
rfm['M_score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5])

rfm[['R_score','F_score','M_score']] = rfm[['R_score','F_score','M_score']].astype(int)

# Segmentation logic
def segment(row):
    if row['R_score'] >= 4 and row['F_score'] >= 4:
        return "Champions"
    elif row['F_score'] >= 4:
        return "Loyal Customers"
    elif row['R_score'] <= 2:
        return "At Risk"
    else:
        return "Potential"

rfm['Segment'] = rfm.apply(segment, axis=1)

# Merge back
df = df.merge(rfm[['Segment']], left_on='Customer ID', right_index=True, how='left')

# ------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------
st.sidebar.header("🔍 Filters")

segment_filter = st.sidebar.multiselect(
    "Customer Segment",
    options=sorted(df["Segment"].dropna().unique()),
    default=sorted(df["Segment"].dropna().unique())
)

region_filter = st.sidebar.multiselect(
    "Region",
    options=sorted(df["Region"].unique()),
    default=sorted(df["Region"].unique())
)

filtered_df = df[
    (df["Segment"].isin(segment_filter)) &
    (df["Region"].isin(region_filter))
]

# ------------------------------------------------
# KPI SECTION
# ------------------------------------------------
total_revenue = filtered_df["Sales"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_customers = filtered_df["Customer ID"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
col2.metric("📦 Total Orders", total_orders)
col3.metric("👥 Total Customers", total_customers)

st.markdown("---")

# ------------------------------------------------
# MONTHLY TREND
# ------------------------------------------------
st.subheader("📈 Monthly Revenue Trend")

monthly = filtered_df.groupby(
    filtered_df["Order Date"].dt.to_period("M")
)["Sales"].sum().reset_index()

monthly["Order Date"] = monthly["Order Date"].astype(str)

fig_trend = px.line(
    monthly,
    x="Order Date",
    y="Sales",
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# ------------------------------------------------
# SEGMENT REVENUE
# ------------------------------------------------
st.subheader("📊 Revenue by Customer Segment")

segment_rev = filtered_df.groupby("Segment")["Sales"].sum().reset_index()

fig_segment = px.bar(
    segment_rev,
    x="Segment",
    y="Sales",
    color="Segment",
    text_auto=True
)

st.plotly_chart(fig_segment, use_container_width=True)

# ------------------------------------------------
# CUSTOMER DISTRIBUTION
# ------------------------------------------------
st.subheader("👥 Customer Distribution")

cust_dist = filtered_df.groupby("Segment")["Customer ID"].nunique().reset_index()

fig_pie = px.pie(
    cust_dist,
    names="Segment",
    values="Customer ID"
)

st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------------
# TOP CUSTOMERS
# ------------------------------------------------
st.subheader("🏆 Top 10 Customers by Revenue")

top_customers = filtered_df.groupby("Customer Name")["Sales"] \
    .sum() \
    .sort_values(ascending=False) \
    .head(10) \
    .reset_index()

st.dataframe(top_customers, use_container_width=True)

# ------------------------------------------------
# DOWNLOAD BUTTON
# ------------------------------------------------
st.markdown("---")
st.subheader("⬇ Export Filtered Dataset")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="rfm_filtered_data.csv",
    mime="text/csv"
)

# ------------------------------------------------
# AUTO BUSINESS INSIGHTS
# ------------------------------------------------
st.markdown("---")
st.subheader("📌 Executive Insights")

if not segment_rev.empty:
    top_seg = segment_rev.sort_values("Sales", ascending=False).iloc[0]

    st.write(f"""
    • **{top_seg['Segment']}** is the highest revenue-generating segment.  
    • Revenue trend supports identifying seasonality for campaign timing.  
    • Segmentation enables targeted retention strategies.  
    • At-risk customers should be prioritized for engagement campaigns.
    """)