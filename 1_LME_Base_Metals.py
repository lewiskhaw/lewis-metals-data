import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
from io import StringIO
from datetime import datetime

# --- CONFIGURATION MATCHING YOUR REPO ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"

# Global date variable initialization to secure regex fallbacks
today_str = datetime.today().strftime('%Y-%m-%d')

# 1. Global Page Layout Setup
st.set_page_config(page_title="LME Base Metals Intelligence", layout="wide", page_icon="🏭")

st.title("🏭 London Metal Exchange (LME) Base Metals Panel")
st.caption("🌐 Global Cloud Engine — Synchronized via Private Bloomberg Core API & Multi-Agent Cognitive Synthesis")

# Create two distinct UI panel views right below the main header
tab1, tab2 = st.tabs(["📊 Live LME Metrics & Charts", "📂 Autonomous AI Case Studies"])

# ==============================================================================
# TAB 1: QUANTITATIVE TRADING DESK METRICS (YOUR RESTORED LOGIC)
# ==============================================================================
with tab1:
    master_df = None
    
    # --- PHASE 1: PREFER LOCAL WORKSPACE LOAD (Fastest & Safest) ---
    local_csv_path = "lme_master_data.csv"
    
    # If the app is inside a subfolder/pages directory, check one level up as well
    if not os.path.exists(local_csv_path):
        local_csv_path = os.path.join("..", "lme_master_data.csv")
        
    if os.path.exists(local_csv_path):
        try:
            master_df = pd.read_csv(local_csv_path)
        except Exception as e:
            st.warning(f"Failed to read local workspace CSV, attempting remote fallback: {e}")

    # --- PHASE 2: REMOTE URL FALLBACK (If Local File is Missing) ---
    if master_df is None:
        if "GITHUB_TOKEN" not in st.secrets:
            st.error("⚠️ GITHUB_TOKEN is missing from your Streamlit App Secrets.")
            st.info("Please go to your Streamlit Cloud Dashboard -> App Settings -> Secrets, and paste: GITHUB_TOKEN = 'your_token'")
        else:
            token = st.secrets["GITHUB_TOKEN"]
            headers = {"Authorization": f"token {token}"}
            
            url_main = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}"
            url_master = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/master/{FILE_PATH}"

            try:
                response = requests.get(url_main, headers=headers)
                if response.status_code == 404:
                    response = requests.get(url_master, headers=headers)
                    
                if response.status_code == 200:
                    master_df = pd.read_csv(StringIO(response.text))
                else:
                    st.error(f"⚠️ Failed to pull data from GitHub. HTTP Status Code: {response.status_code}")
                    st.info("Verify that lme_master_data.csv exists in your repository branch.")
            except Exception as e:
                st.error(f"❌ Remote Data Stream Error: {e}")

    # --- PHASE 3: RENDER VISUALIZATION METRICS ---
    if master_df is not None:
        try:
            # Force columns to lowercase and remove spaces
            master_df.columns = [str(col).lower().strip() for col in master_df.columns]
            
            col_date = 'date'
            col_metal = 'metal'
            
            if 'cash_bid' in master_df.columns and 'cash_ask' in master_df.columns:
                master_df['cash_mid'] = (master_df['cash_bid'] + master_df['cash_ask']) / 2
                col_close = 'cash_mid'
            else:
                col_close = master_df.columns[2]
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy()
            df_metal[col_date] = pd.to_datetime(df_metal[col_date])
            df_metal = df_metal.sort_values(by=col_date).reset_index(drop=True)
            
            if not df_metal.empty:
                # --- CALCULATION OF LIVE OVERLAYS FOR THE WEB DASHBOARD ---
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                current_price = float(df_metal[col_close].iloc[-1])
                
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_close].iloc[-2])
                    price_delta = current_price - prior_price
                    pct_delta = (price_delta / prior_price) * 100
                else:
                    price_delta, pct_delta = 0.0, 0.0
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"LME {metal_selection} Cash Mid Price", f"${current_price:,.2f}", f"{price_delta:+,.2f} ({pct_delta:+.2f}%)" if len(df_metal) > 1 else "0.00 (
