
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from io import BytesIO

# Load Excel data
df = pd.read_excel("Book_with_Coordinates.xlsx")

# Clean and prep data
df = df.dropna(subset=["Cust City", "Cust Zip", "Parent Company", "Policy Type LOB", "Dwelling Limit", "Latitude", "Longitude"])
df["CovA"] = pd.to_numeric(df["Dwelling Limit"], errors="coerce")
df["Cust Zip"] = df["Cust Zip"].astype(str).str[:5]

# Sidebar filters
st.sidebar.title("🗂 Filter Options")
parent_filter = st.sidebar.multiselect("Select Parent Company", sorted(df["Parent Company"].unique()), default=df["Parent Company"].unique())
lob_filter = st.sidebar.multiselect("Select Line of Business", sorted(df["Policy Type LOB"].unique()), default=df["Policy Type LOB"].unique())

filtered_df = df[df["Parent Company"].isin(parent_filter) & df["Policy Type LOB"].isin(lob_filter)]

# Title and logo
st.image("brightway_logo.png", width=300)
st.title("🏡 Property Aggregation Management — Underwriting Dashboard")

# Total CovA
total_covA = filtered_df["CovA"].sum()
st.metric(label="Total CovA (Filtered)", value=f"${total_covA:,.0f}")

# Carrier comparison
carrier_summary = filtered_df.groupby("Parent Company").agg(
    TotalCovA=("CovA", "sum"),
    PolicyCount=("CovA", "count")
).reset_index().sort_values(by="TotalCovA", ascending=False)

st.subheader("🏢 Carrier Comparison")
st.dataframe(carrier_summary)

# CovA by Zip Code
zip_summary = filtered_df.groupby("Cust Zip").agg(
    TotalCovA=("CovA", "sum"),
    PolicyCount=("CovA", "count")
).reset_index().sort_values(by="TotalCovA", ascending=False)

st.subheader("📍 Top ZIP Codes by Total CovA")
st.dataframe(zip_summary.head(10))

# Map with color-coded markers
m = folium.Map(location=[31.0, -99.0], zoom_start=6, tiles="Cartodb Positron")
marker_cluster = MarkerCluster().add_to(m)

def cova_color(value):
    if value >= 750000:
        return "red"
    elif value >= 400000:
        return "orange"
    else:
        return "green"

grouped = filtered_df.groupby(["Cust City", "Latitude", "Longitude"]).agg(TotalCovA=("CovA", "sum")).reset_index()

for _, row in grouped.iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=8,
        color=cova_color(row["TotalCovA"]),
        fill=True,
        fill_color=cova_color(row["TotalCovA"]),
        fill_opacity=0.7,
        popup=f"City: {row['Cust City']}<br>Total CovA: ${row['TotalCovA']:,.0f}"
    ).add_to(marker_cluster)

st.subheader("🗺️ Property Aggregation Map")
st_data = st_folium(m, width=700, height=500)

# Export data to CSV
st.subheader("⬇️ Export Filtered Data")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered Data as CSV", data=csv, file_name="Filtered_Book_of_Business.csv", mime="text/csv")

