import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="RFM Dashboard", layout="wide")

st.title("📊 Customer Segmentation Dashboard (RFM Analysis)")

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_csv("Superstore.csv", encoding="latin1")
df['Order Date'] = pd.to_datetime(df['Order Date'])

snapshot_date = df['Order Date'].max() + pd.Timedelta(days=1)

# -------------------------
# BUILD RFM
# -------------------------
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

# -------------------------
# SIDEBAR FILTER
# -------------------------
st.sidebar.header("Filters")

selected_segment = st.sidebar.multiselect(
    "Select Segment",
    options=rfm["Segment"].unique(),
    default=rfm["Segment"].unique()
)

rfm_filtered = rfm[rfm["Segment"].isin(selected_segment)]

# -------------------------
# KPIs
# -------------------------
total_revenue = df['Sales'].sum()
total_customers = rfm_filtered.shape[0]
avg_order_value = df['Sales'].mean()

col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Customers", total_customers)
col3.metric("Average Order Value", f"${avg_order_value:,.2f}")

# -------------------------
# Revenue by Segment
# -------------------------
segment_revenue = rfm_filtered.merge(df[['Customer ID','Sales']], on='Customer ID')
segment_revenue = segment_revenue.groupby('Segment')['Sales'].sum().reset_index()

fig1 = px.bar(segment_revenue,
              x='Segment',
              y='Sales',
              title="Revenue by Segment")

st.plotly_chart(fig1, use_container_width=True)

# -------------------------
# RFM Heatmap
# -------------------------
heatmap_data = rfm_filtered.groupby('Segment')[['R_score','F_score','M_score']].mean()

fig2 = px.imshow(
    heatmap_data,
    title="Average RFM Scores by Segment",
    aspect="auto"
)

st.plotly_chart(fig2, use_container_width=True)

#Add Business Insight Section

st.markdown("---")
st.subheader("📌 Key Business Insights")

top_segment = segment_revenue.sort_values("Sales", ascending=False).iloc[0]

st.write(f"""
• The highest revenue generating segment is **{top_segment['Segment']}**  
• Total revenue: **${total_revenue:,.0f}**  
• Total customers analyzed: **{total_customers}**  
• High RFM segments contribute significantly to overall revenue.
""")

#Add Top 10 Customers Table

st.subheader("🏆 Top 10 Customers by Revenue")

top_customers = rfm_filtered.sort_values("Monetary", ascending=False).head(10)

st.dataframe(top_customers)

#Add Download Button

csv = rfm_filtered.to_csv(index=False)

st.download_button(
    label="📥 Download Filtered Data",
    data=csv,
    file_name="rfm_filtered_data.csv",
    mime="text/csv"
)

#Clean Executive Title

st.title("📊 Executive Customer Segmentation Dashboard")
st.markdown("RFM Analysis on Superstore Dataset | Built with Python, Streamlit & Plotly")

