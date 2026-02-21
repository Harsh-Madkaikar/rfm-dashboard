import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="RFM Dashboard", layout="wide")

st.title("📊 RFM Customer Segmentation Dashboard")

# ==============================
# Project Description
# ==============================
st.markdown("""
## 📌 Project Overview

This dashboard performs **RFM (Recency, Frequency, Monetary) Analysis**
to segment customers based on purchasing behavior.

### 🎯 Business Objective:
- Identify high-value customers
- Improve retention strategies
- Enable targeted marketing campaigns
- Analyze revenue contribution by segment
""")

# ==============================
# Load Data
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("Superstore.csv", encoding='latin-1')
    return df

df = load_data()

# Convert date column
df['Order Date'] = pd.to_datetime(df['Order Date'])

# ==============================
# Sidebar Filters
# ==============================
st.sidebar.header("🔍 Filter Data")

segment_filter = st.sidebar.multiselect(
    "Select Segment",
    options=df["Segment"].unique(),
    default=df["Segment"].unique()
)

region_filter = st.sidebar.multiselect(
    "Select Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

filtered_df = df[
    (df["Segment"].isin(segment_filter)) &
    (df["Region"].isin(region_filter))
]

# ==============================
# KPI Metrics
# ==============================
total_sales = filtered_df["Sales"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_customers = filtered_df["Customer ID"].nunique()

col1, col2, col3 = st.columns(3)

col1.metric("💰 Total Sales", f"${total_sales:,.0f}")
col2.metric("📦 Total Orders", total_orders)
col3.metric("👥 Total Customers", total_customers)

# ==============================
# Monthly Sales Trend
# ==============================
st.subheader("📈 Monthly Sales Trend")

sales_trend = filtered_df.groupby(
    filtered_df['Order Date'].dt.to_period("M")
)['Sales'].sum().reset_index()

sales_trend['Order Date'] = sales_trend['Order Date'].astype(str)

fig_trend = px.line(
    sales_trend,
    x="Order Date",
    y="Sales",
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# ==============================
# Revenue by Segment
# ==============================
st.subheader("📊 Revenue by Segment")

segment_revenue = filtered_df.groupby("Segment")["Sales"].sum().reset_index()

fig_segment = px.bar(
    segment_revenue,
    x="Segment",
    y="Sales",
    color="Segment"
)

st.plotly_chart(fig_segment, use_container_width=True)

# ==============================
# Revenue Contribution %
# ==============================
st.subheader("💰 Revenue Contribution by Segment")

total_revenue = segment_revenue["Sales"].sum()

for index, row in segment_revenue.iterrows():
    percent = (row["Sales"] / total_revenue) * 100
    st.write(f"**{row['Segment']}**: {percent:.2f}% of total revenue")

# ==============================
# Top 10 Customers
# ==============================
st.subheader("🏆 Top 10 Customers by Revenue")

top_customers = filtered_df.groupby("Customer Name")["Sales"] \
    .sum() \
    .sort_values(ascending=False) \
    .head(10) \
    .reset_index()

st.dataframe(top_customers)

# ==============================
# Download Button
# ==============================
st.subheader("⬇ Download Filtered Data")

csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)