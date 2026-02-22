import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Executive Customer Segmentation Dashboard", layout="wide")

st.title("📊 Executive Customer Segmentation Dashboard")
st.markdown("RFM-Based Behavioral Analytics | Production-Style Interactive Dashboard")

# -------------------------
# AUTO LOAD DEFAULT DATASET
# -------------------------
@st.cache_data
def load_default_data():
    try:
        file_path = os.path.join(os.getcwd(), "data.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding="ISO-8859-1")
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Error loading default dataset: {e}")
        return None


uploaded_file = st.file_uploader("Upload your dataset (optional)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
    st.success("Custom dataset loaded successfully!")
else:
    df = load_default_data()
    if df is not None:
        st.info("Using default dataset (data.csv)")
    else:
        st.error("No dataset found. Please upload a CSV file.")
        st.stop()

# =====================================================
# VALIDATION
# =====================================================
required_columns = ["CustomerID", "InvoiceDate", "InvoiceNo", "Quantity", "UnitPrice"]

missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.stop()

# =====================================================
# DATA PREPARATION
# =====================================================
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df = df.dropna(subset=["InvoiceDate"])

df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]

snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = df.groupby("CustomerID").agg({
    "InvoiceDate": lambda x: (snapshot_date - x.max()).days,
    "InvoiceNo": "nunique",
    "TotalAmount": "sum"
}).reset_index()

rfm.columns = ["CustomerID", "Recency", "Frequency", "Monetary"]

# =====================================================
# SAFE RFM SCORING
# =====================================================
def safe_qcut(series, labels):
    try:
        return pd.qcut(series, 4, labels=labels, duplicates="drop")
    except:
        return pd.Series([labels[0]] * len(series))

rfm["R_Score"] = safe_qcut(rfm["Recency"], [4,3,2,1])
rfm["F_Score"] = safe_qcut(rfm["Frequency"].rank(method="first"), [1,2,3,4])
rfm["M_Score"] = safe_qcut(rfm["Monetary"], [1,2,3,4])

rfm["RFM_Score"] = (
    rfm["R_Score"].astype(str) +
    rfm["F_Score"].astype(str) +
    rfm["M_Score"].astype(str)
)

# =====================================================
# SEGMENT LOGIC
# =====================================================
def segment_customer(score):
    if score in ["444","443","434","433"]:
        return "Champions"
    elif score in ["344","343","334"]:
        return "Loyal Customers"
    elif score in ["244","243","234"]:
        return "Potential Loyalist"
    elif score in ["144","143"]:
        return "New Customers"
    elif score in ["111","112","121"]:
        return "At Risk"
    else:
        return "Others"

rfm["Segment"] = rfm["RFM_Score"].apply(segment_customer)

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("🔍 Filters")

segment_options = sorted(rfm["Segment"].unique())

selected_segment = st.sidebar.selectbox(
    "Select Segment",
    options=["All"] + segment_options
)

if selected_segment != "All":
    filtered_rfm = rfm[rfm["Segment"] == selected_segment]
else:
    filtered_rfm = rfm

# =====================================================
# KPIs
# =====================================================
st.subheader("📌 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Customers", filtered_rfm["CustomerID"].nunique())
col2.metric("Avg Recency (Days)", round(filtered_rfm["Recency"].mean(), 1))
col3.metric("Avg Frequency", round(filtered_rfm["Frequency"].mean(), 1))
col4.metric("Total Revenue", f"${round(filtered_rfm['Monetary'].sum(),2):,}")

# =====================================================
# SEGMENT DISTRIBUTION
# =====================================================
st.subheader("📊 Customer Segment Distribution")

segment_counts = filtered_rfm["Segment"].value_counts().reset_index()
segment_counts.columns = ["Segment", "Count"]

fig1 = px.bar(
    segment_counts,
    x="Segment",
    y="Count",
    color="Segment",
    title="Customer Count by Segment"
)

st.plotly_chart(fig1, use_container_width=True)

# =====================================================
# RFM SCATTER
# =====================================================
st.subheader("📈 RFM Scatter Analysis")

fig2 = px.scatter(
    filtered_rfm,
    x="Recency",
    y="Monetary",
    size="Frequency",
    color="Segment",
    hover_data=["CustomerID"],
    title="Recency vs Monetary (Bubble Size = Frequency)"
)

st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# TOP CUSTOMERS
# =====================================================
st.subheader("🏆 Top 10 High-Value Customers")

top_customers = filtered_rfm.sort_values("Monetary", ascending=False).head(10)
st.dataframe(top_customers, use_container_width=True)

# =====================================================
# DOWNLOAD
# =====================================================
csv = filtered_rfm.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data",
    data=csv,
    file_name="filtered_rfm.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown("Developed for Executive-Level Customer Intelligence & Data-Driven Decision Making")