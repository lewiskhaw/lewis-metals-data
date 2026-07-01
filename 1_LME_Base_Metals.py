import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
import json
from io import StringIO
from datetime import datetime, timedelta

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
            # Strip spaces and normalize headers
            master_df.columns = [str(c).lower().strip() for c in master_df.columns]
            col_date, col_metal = 'date', 'metal'
            master_df[col_date] = pd.to_datetime(master_df[col_date], errors='coerce')
            master_df = master_df.dropna(subset=[col_date])
            
            # Logic for calculations
            master_df['calc_cash_bid'] = pd.to_numeric(master_df['cash_bid'], errors='coerce').fillna(0.0)
            master_df['calc_cash_ask'] = pd.to_numeric(master_df['cash_ask'], errors='coerce').fillna(0.0)
            master_df['calc_cash_mid'] = (master_df['calc_cash_bid'] + master_df['calc_cash_ask']) / 2
            
            mb_key = 'px_bid.1' if 'px_bid.1' in master_df.columns else '3m_bid'
            ma_key = 'px_ask.1' if 'px_ask.1' in master_df.columns else '3m_ask'
            master_df['calc_3m_bid'] = pd.to_numeric(master_df[mb_key], errors='coerce').fillna(0.0)
            master_df['calc_3m_ask'] = pd.to_numeric(master_df[ma_key], errors='coerce').fillna(0.0)
            
            moc_key = 'c_3m_moc' if 'c_3m_moc' in master_df.columns else 'px_last.1'
            master_df['calc_c_3m_moc'] = pd.to_numeric(master_df[moc_key], errors='coerce').fillna(0.0)

            metal_selection = st.selectbox("Select Target Base Metal to Analyze", ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"], key="tab1_metal_select")
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy().sort_values(by=col_date)
            
            if not df_metal.empty:
                # 🎯 Pre-calculate SMAs globally
                df_metal['sma_20'] = df_metal['calc_cash_mid'].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal['calc_cash_mid'].rolling(window=50).mean()

                # Metrics display... (Your existing m_col1-5 code goes here)
                # ... [Keep your m_col1-5 metric code exactly as you had it] ...
                
                # --- TIME SELECTION ---
                timeframe = st.radio("Select Chart Timeframe:", ["1W", "1M", "YTD", "1Y", "3Y", "5Y", "10Y", "ALL"], index=1, horizontal=True)
                max_date = df_metal[col_date].max()
                
                # Slicing
                df_chart = df_metal.copy()
                if timeframe == "1W": df_chart = df_chart[df_chart[col_date] >= (max_date - timedelta(weeks=1))]
                elif timeframe == "1M": df_chart = df_chart[df_chart[col_date] >= (max_date - timedelta(days=30))]
                elif timeframe == "YTD": df_chart = df_chart[df_chart[col_date].dt.year == max_date.year]
                elif timeframe == "1Y": df_chart = df_chart[df_chart[col_date] >= (max_date - timedelta(days=365))]
                # ... (add other logic)
                
                # 📊 CHART
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['calc_cash_mid'], name="Cash Mid Price"))
                # Plotly autoscales if we don't fix y-axis range
                fig.update_layout(height=500, template="plotly_white", yaxis=dict(tickformat="$,.0f"))
                st.plotly_chart(fig, use_container_width=True)

                # 🔍 LEDGERS
                with st.expander("🔍 View Raw Ingestion Ledger & Monthly Averages"):
                    # Existing Ledger
                    st.dataframe(df_metal.sort_values(by=col_date, ascending=False), use_container_width=True)
                    
                    # 📈 NEW MONTHLY AVERAGES SECTION
                    st.markdown("### 📅 Monthly Average Pricing Analysis")
                    df_monthly = df_metal.copy()
                    df_monthly['Date'] = pd.to_datetime(df_monthly[col_date])
                    monthly_avg = df_monthly.groupby(pd.Grouper(key='Date', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean()
                    monthly_avg.columns = ['Avg 2RC Cash Ask', 'Avg 2RC 3M Ask']
                    st.dataframe(monthly_avg.style.format("${:,.2f}"), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")
