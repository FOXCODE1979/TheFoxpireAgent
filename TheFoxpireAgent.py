
import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="TheFoxpireAgent", layout="wide")

st.title("🦊 TheFoxpireAgent – Portfolio AI Monitor")

uploaded_file = st.file_uploader("📤 Upload your master portfolio CSV", type=["csv"])

FX_RATES = {"EUR": 1.0, "USD": 0.93, "AED": 0.25}

def calculate(df):
    for col in ["Shares", "Price_Local", "Value_Local", "Buy_Price_Local", "Buy_Value_Local"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["FX"] = df["Currency"].map(FX_RATES).fillna(1.0)
    df["Value_EUR"] = df["Value_Local"] * df["FX"]
    df["Buy_Value_EUR"] = df["Buy_Value_Local"] * df["FX"]
    df["Gain_%"] = (df["Value_EUR"] - df["Buy_Value_EUR"]) / df["Buy_Value_EUR"] * 100
    df["Portfolio_%"] = df["Value_EUR"] / df["Value_EUR"].sum() * 100
    return df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = calculate(df)

    st.subheader("📊 Portfolio Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total EUR Value", f"{df['Value_EUR'].sum():,.2f} €")
    col2.metric("Tracked Assets", len(df))

    st.subheader("📈 Top Gainers")
    st.dataframe(df.sort_values("Gain_%", ascending=False).head(5)[["Name", "Value_EUR", "Gain_%", "Portfolio_%"]])

    st.subheader("📉 Top Losers")
    st.dataframe(df.sort_values("Gain_%", ascending=True).head(5)[["Name", "Value_EUR", "Gain_%", "Portfolio_%"]])

    st.subheader("📋 Full Portfolio")
    st.dataframe(df.sort_values("Portfolio_%", ascending=False))

    st.download_button("⬇️ Download Excel Export", to_excel(df), file_name="foxpire_portfolio_export.xlsx")

else:
    st.info("Upload a portfolio CSV to get started.")
