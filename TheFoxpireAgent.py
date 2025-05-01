
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import requests
from twilio.rest import Client

# === CONFIG ===
CSV_URL = "https://raw.githubusercontent.com/FOXCODE1979/TheFoxpireAgent/main/master_portfolio_currency_aware.csv"
FX_RATES = {"EUR": 1.0, "USD": 0.93, "AED": 0.25}

TWILIO_SID = "AC5b4107ae4c334976e6babd6c2eb3ba36"
TWILIO_AUTH = "f4ba3c50fd98a9dc663f054b3ce2416b"
TWILIO_FROM = "whatsapp:+14155238886"
TO_NUMBER = "whatsapp:+971585663878"

st.set_page_config(page_title="TheFoxpireAgent", layout="wide")
st.title("🦊 TheFoxpireAgent – AI Investment Monitor")

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(CSV_URL)
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

def generate_summary(df):
    lines = [f"📊 Portfolio Update ({datetime.now().strftime('%Y-%m-%d %H:%M')}):"]
    top_gainers = df.sort_values("Gain_%", ascending=False).head(2)
    top_losers = df.sort_values("Gain_%", ascending=True).head(2)
    for _, row in top_gainers.iterrows():
        lines.append(f"🟢 {row['Name']}: up {row['Gain_%']:.1f}%")
    for _, row in top_losers.iterrows():
        lines.append(f"🔴 {row['Name']}: down {row['Gain_%']:.1f}%")
    total = df["Value_EUR"].sum()
    lines.append(f"💰 Total EUR Value: €{total:,.0f}")
    return "\n".join(lines)

def send_whatsapp(message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        msg = client.messages.create(body=message, from_=TWILIO_FROM, to=TO_NUMBER)
        return f"✅ Sent! SID: {msg.sid}"
    except Exception as e:
        return f"❌ Failed: {e}"

df = load_data()

if df is not None:
    st.subheader("📊 Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total EUR Value", f"{df['Value_EUR'].sum():,.2f} €")
    col2.metric("Assets", len(df))

    st.subheader("📈 Top Gainers")
    st.dataframe(df.sort_values("Gain_%", ascending=False).head(5)[["Name", "Gain_%", "Value_EUR"]])

    st.subheader("📉 Top Losers")
    st.dataframe(df.sort_values("Gain_%", ascending=True).head(5)[["Name", "Gain_%", "Value_EUR"]])

    st.subheader("📋 Full Portfolio")
    st.dataframe(df)

    if st.button("📲 Send WhatsApp Alert Now"):
        summary = generate_summary(df)
        result = send_whatsapp(summary)
        st.success(result)

    st.download_button("⬇️ Export Excel", to_excel(df), file_name="foxpire_export.xlsx")
else:
    st.warning("Could not load portfolio data.")
