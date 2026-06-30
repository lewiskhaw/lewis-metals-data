import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from io import StringIO

# --- CONFIGURATION MATCHING YOUR REPO ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"

st.set_page_config(page_title="LME Base Metals Intelligence", layout="wide", page_icon="🏭")

st.title("🏭 London Metal Exchange (LME) Base Metals Panel")
st.caption("🌐 Global Cloud Engine — Synchronized via Private Bloomberg Core API")
st.markdown("---")

# Securely grab the token you saved in the Streamlit Advanced Settings
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ GITHUB_TOKEN is missing from your Streamlit App Secrets.")
    st.info("Please go to your Streamlit Cloud Dashboard -> App Settings -> Secrets, and paste: GITHUB_TOKEN = 'your_token'")
else:
    token = st.secrets["GITHUB_TOKEN"]
    url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}"
    headers = {"Authorization": f"token {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            master_df = pd.read_csv(StringIO(response.text))
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS)
            
            df_metal = master_df[master_df['metal'] == metal_selection].copy()
            df_metal['date'] = pd.to_datetime(df_metal['date'])
            df_metal = df_metal.sort_values(by='date').reset_index(drop=True)
            
            if not df_metal.empty:
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
                fig_candle.update_layout(xaxis_rangeslider_visible=False, height=380, template="plotly_white", margin=dict(t=40, b=10))
                st.plotly_chart(fig_candle, use_container_width=True)
            else:
                st.warning("Data file found, but requested asset classes are empty.")
        else:
            st.error(f"⚠️ Failed to pull data from GitHub. HTTP Status Code: {response.status_code}")
            st.info("Verify your GITHUB_TOKEN secret has access to this private repository.")
    except Exception as e:
        st.error(f"❌ Data Stream Error: {e}")
