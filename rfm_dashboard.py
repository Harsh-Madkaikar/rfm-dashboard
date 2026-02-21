import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Executive RFM Dashboard", layout="wide")

st.title("📊 Executive Customer Segmentation Dashboard")
st.markdown("""
### RFM-Based Customer Analytics | Built with Python, Pandas & Streamlit

This dashboard applies **RFM (Recency, Frequency, Monetary) Analysis**
to segment customers based on purchasing behavior and revenue contribution.

#### 🎯 Business Objective:
- Identify high-value customers
- Improve retention strategy
- Enable targeted marketing campaigns
- Analyze revenue trends and segment performance
""")

# ==============================
# Load Data
# ==============================
@st.cache_data
def load_data():
    df = pd.read_csv("Superstore.csv", encoding="latin1")
    return df

df = load_data()
df['Order Date'] = pd.to_datetime(df['Order Date'])

# ==============================
# Build RFM
# ==============================
snapshot_date = df['Order Date'].max() + pd.Timedelta(days=1)

rfm = df.groupby('Customer ID').agg({
    'Order Date': lambda x: (snapshot_date - x.max()).days,
    'Customer ID': 'count',
    'Sales': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

rfm['R_score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1]).astype(int)
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
rfm['M_score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5]).astype(int)

def segment(row):
    if row['R_score'] >= 4 and row['F_score'] >= 4 and row['M_score'] >= 4:
        return 'Champions'
    elif row['F_score'] >= 4 and row['M_score'] >= 3:
        return 'Loyal Customers'
    elif row['M_score'] >= 4:
        return 'Big Spenders'
    elif row['R_score'] == 5:
        return 'New Customers'
    elif row['R_score'] <= 2 and row['F_score'] >= 3:
        return 'At Risk'
    elif row['R_score'] == 1:
        return 'Lost Customers'
    else:
        return 'Potential Loyalists'

rfm['Segment'] = rfm.apply(segment, axis=1)

df = df.merge(rfm[['Segment']], left_on='Customer ID', right_index=True)

# ==============================
# Sidebar Filters
# ==============================
st.sidebar.header("🔍 Filters")

selected_segment = st.sidebar.multiselect(
    "Select Segment",
    options=df["Segment"].unique(),
    default=df["Segment"].unique()
)

selected_region = st.sidebar.multiselect(
    "Select Region",
    options=df["Region"].unique(),
    default=df["Region"].unique()
)

filtered_df = df[
    (df["Segment"].isin(selected_segment)) &
    (df["Region"].isin(selected_region))
]

# ==============================
# KPI Metrics
# ==============================
total_sales = filtered_df["Sales"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_customers = filtered_df["Customer ID"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue", f"${total_sales:,.0f}")
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

fig_trend = px.line(sales_trend, x="Order Date", y="Sales", markers=True)
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

for _, row in segment_revenue.iterrows():
    percent = (row["Sales"] / total_revenue) * 100
    st.write(f"**{row['Segment']}**: {percent:.2f}% of total revenue")

# ==============================
# Customer Distribution
# ==============================
st.subheader("👥 Customer Distribution by Segment")

customer_dist = filtered_df.groupby("Segment")["Customer ID"].nunique().reset_index()

fig_pie = px.pie(
    customer_dist,
    names="Segment",
    values="Customer ID"
)
st.plotly_chart(fig_pie, use_container_width=True)

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

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="rfm_filtered_data.csv",
    mime="text/csv"
)

# ==============================
# Key Insights Section
# ==============================
st.markdown("---")
st.subheader("📌 Key Business Insights")

top_segment = segment_revenue.sort_values("Sales", ascending=False).iloc[0]

st.write(f"""
• The highest revenue generating segment is **{top_segment['Segment']}**  
• Revenue concentration highlights importance of customer retention  
• Monthly trend visualization supports seasonal strategy planning  
• RFM segmentation enables data-driven marketing decisions  
""")