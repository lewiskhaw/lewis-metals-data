import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
import json
from io import StringIO
from datetime import datetime

# --- CONFIGURATION ENGINE ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"

today_str = datetime.today().strftime('%Y-%m-%d')

# 1. Global Page Layout Setup
st.set_page_config(page_title="LME Base Metals Intelligence", layout="wide", page_icon="🏭")

st.title("🏭 London Metal Exchange (LME) Base Metals Panel")
st.caption("🌐 Global Cloud Engine — Synchronized via Private Bloomberg Core API & Multi-Agent Cognitive Synthesis")

tab1, tab2 = st.tabs(["📊 Live LME Metrics & Charts", "📂 Autonomous AI Case Studies"])

# ==============================================================================
# TAB 1: QUANTITATIVE TRADING DESK METRICS
# ==============================================================================
with tab1:
    master_df = None
    
    if "GITHUB_TOKEN" not in st.secrets:
        st.error("⚠️ GITHUB_TOKEN is missing from your Streamlit App Secrets.")
    else:
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        url_main = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}"
        url_master = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/master/{FILE_PATH}"

        try:
            cb_url = f"{url_main}?cb={int(datetime.now().timestamp())}"
            response = requests.get(cb_url, headers=headers)
            
            if response.status_code == 404:
                cb_master = f"{url_master}?cb={int(datetime.now().timestamp())}"
                response = requests.get(cb_master, headers=headers)
                
            if response.status_code == 200:
                master_df = pd.read_csv(StringIO(response.text))
            else:
                st.error(f"⚠️ Failed to pull live data matrix from GitHub. Status Code: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Remote Data Stream Connection Error: {e}")

    if master_df is not None:
        try:
            # Strip spaces and normalize headers to lowercase
            master_df.columns = [str(c).lower().strip() for c in master_df.columns]
            
            col_date = 'date'
            col_metal = 'metal'
            
            master_df[col_date] = pd.to_datetime(master_df[col_date], errors='coerce')
            master_df = master_df.dropna(subset=[col_date])
            
            # 🎯 HARDENED ALIGNMENT LAYER
            # 1. Parse Cash prompt metrics
            master_df['calc_cash_bid'] = pd.to_numeric(master_df['cash_bid'] if 'cash_bid' in master_df.columns else pd.Series([0.0]*len(master_df)), errors='coerce').fillna(0.0)
            master_df['calc_cash_ask'] = pd.to_numeric(master_df['cash_ask'] if 'cash_ask' in master_df.columns else pd.Series([0.0]*len(master_df)), errors='coerce').fillna(0.0)
            master_df['calc_cash_mid'] = (master_df['calc_cash_bid'] + master_df['calc_cash_ask']) / 2
            
            # 2. Parse 3-Month prompt metrics
            mb_key = 'px_bid.1' if 'px_bid.1' in master_df.columns else ('3m_bid' if '3m_bid' in master_df.columns else master_df.columns[3])
            ma_key = 'px_ask.1' if 'px_ask.1' in master_df.columns else ('3m_ask' if '3m_ask' in master_df.columns else master_df.columns[4])
            
            master_df['calc_3m_bid'] = pd.to_numeric(master_df[mb_key] if mb_key in master_df.columns else pd.Series([0.0]*len(master_df)), errors='coerce').fillna(0.0)
            master_df['calc_3m_ask'] = pd.to_numeric(master_df[ma_key] if ma_key in master_df.columns else pd.Series([0.0]*len(master_df)), errors='coerce').fillna(0.0)
            master_df['calc_3m_mid'] = (master_df['calc_3m_bid'] + master_df['calc_3m_ask']) / 2
            
            # 3. Parse Injected C-3M MOC Column
            moc_key = None
            for candidate in ['c_3m_moc', 'c-3m moc', 'c-3m_moc', 'c_3m_moc.1', 'px_last.1']:
                if candidate in master_df.columns:
                    moc_key = candidate
                    break
            
            if moc_key:
                master_df['calc_c_3m_moc'] = pd.to_numeric(master_df[moc_key], errors='coerce').fillna(0.0)
            else:
                master_df['calc_c_3m_moc'] = pd.to_numeric(master_df.iloc[:, 5] if len(master_df.columns) > 5 else pd.Series([0.0]*len(master_df)), errors='coerce').fillna(0.0)

            col_close = 'calc_cash_mid'
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy()
            df_metal = df_metal.sort_values(by=col_date, ascending=True).reset_index(drop=True)
            
            if not df_metal.empty:
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                # Extract terminal target prices cleanly for layout calculations
                latest_row = df_metal.iloc[-1]
                current_cash_bid = float(latest_row['calc_cash_bid'])
                current_cash_ask = float(latest_row['calc_cash_ask'])
                current_3m_bid = float(latest_row['calc_3m_bid'])
                current_3m_ask = float(latest_row['calc_3m_ask'])
                current_c_3m_moc = float(latest_row['calc_c_3m_moc'])
                current_cash_mid = float(latest_row['calc_cash_mid'])
                
                # Dynamic performance string indicators based on mid variance
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_close].iloc[-2])
                    price_delta = current_cash_mid - prior_price
                    pct_delta = (price_delta / prior_price) * 100 if prior_price != 0 else 0.0
                    delta_string = f"{price_delta:+,.2f} ({pct_delta:+.2f}%)"
                else:
                    delta_string = "0.00 (0.00%)"
                
                # 📊 5-COLUMN REBRANDED PREMIUM METRICS INDICATOR LAYER
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                m_col1.metric(f"LME {metal_selection} 2RC Cash Bid", f"${current_cash_bid:,.2f}", delta_string)
                m_col2.metric(f"LME {metal_selection} 2RC Cash Ask", f"${current_cash_ask:,.2f}")
                m_col3.metric(f"LME {metal_selection} 2RC 3M Bid", f"${current_3m_bid:,.2f}")
                m_col4.metric(f"LME {metal_selection} 2RC 3M Ask", f"${current_3m_ask:,.2f}")
