import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(page_title="LME Base Metals Intelligence", layout="wide", page_icon="🏭")

st.title("🏭 London Metal Exchange (LME) Base Metals Panel")
st.caption("🌐 Global Cloud Engine — Debug Mode")
st.markdown("---")

# --- STEP 1: TEST SECRETS ENGINE ---
if "GITHUB_TOKEN" not in st.secrets:
    st.error("❌ Configuration Error: `GITHUB_TOKEN` was not found inside your Streamlit Cloud Secrets box.")
    st.info("💡 To fix this: Go to share.streamlit.io -> Click the 3 dots next to your app -> Settings -> Secrets -> Paste: `GITHUB_TOKEN = 'your_token_here'`")
    st.stop()

# --- STEP 2: TEST DATA RESOLVER ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"
token = st.secrets["GITHUB_TOKEN"]

url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}"
headers = {"Authorization": f"token {token}"}

st.info("🔄 Attempting to fetch CSV data array from private cloud repository...")

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        st.success("✅ Secure connection established! Parsing matrix...")
        master_df = pd.read_csv(StringIO(response.text))
        
        METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
        metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS)
        
        df_metal = master_df[master_df['metal'] == metal_selection].copy()
        df_metal['date'] = pd.to_datetime(df_metal['date'])
        df_metal = df_metal.sort_values(by='date').reset_index(drop=True)
        
        current_price = df_metal['close'].iloc[-1]
        prior_price = df_metal['close'].iloc[-2]
        price_delta = current_price - prior_price
        pct_delta = (price_delta / prior_price) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric(f"LME {metal_selection} Price", f"${current_price:,.2f}", f"{price_delta:+,.2f} ({pct_delta:+.2f}%)")
        col2.metric("Data Engine Status", "Cloud Synced (Active)")
        col3.metric("Last Data Update", df_metal['date'].iloc[-1].strftime('%Y-%m-%d'))
        
        fig_candle = go.Figure(data=[go.Candlestick(
            x=df_metal['date'], open=df_metal['open'], high=df_metal['high'], low=df_metal['low'], close=df_metal['close'], name=metal_selection
        )])
        fig_candle.update_layout(xaxis_rangeslider_visible=False, height=380, template="plotly_white")
        st.plotly_chart(fig_candle, use_container_width=True)
    else:
        st.error(f"❌ GitHub API Error: Server returned HTTP status code {response.status_code}")
        if response.status_code == 404:
            st.warning("💡 Double check that your file name is exactly `lme_master_data.csv` and that it is located in the main root folder of your repo.")
except Exception as e:
    st.error(f"❌ Critical Data Runtime Error: {e}")
