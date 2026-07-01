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
            master_df.columns = [str(c).lower().strip() for c in master_df.columns]
            col_date, col_metal = 'date', 'metal'
            master_df[col_date] = pd.to_datetime(master_df[col_date], errors='coerce')
            master_df = master_df.dropna(subset=[col_date])
            
            # --- CALCULATIONS ---
            master_df['calc_cash_bid'] = pd.to_numeric(master_df['cash_bid'] if 'cash_bid' in master_df.columns else 0.0, errors='coerce').fillna(0.0)
            master_df['calc_cash_ask'] = pd.to_numeric(master_df['cash_ask'] if 'cash_ask' in master_df.columns else 0.0, errors='coerce').fillna(0.0)
            master_df['calc_cash_mid'] = (master_df['calc_cash_bid'] + master_df['calc_cash_ask']) / 2
            
            mb_key = 'px_bid.1' if 'px_bid.1' in master_df.columns else '3m_bid'
            ma_key = 'px_ask.1' if 'px_ask.1' in master_df.columns else '3m_ask'
            master_df['calc_3m_bid'] = pd.to_numeric(master_df[mb_key] if mb_key in master_df.columns else 0.0, errors='coerce').fillna(0.0)
            master_df['calc_3m_ask'] = pd.to_numeric(master_df[ma_key] if ma_key in master_df.columns else 0.0, errors='coerce').fillna(0.0)
            master_df['calc_c_3m_moc'] = pd.to_numeric(master_df['c_3m_moc'] if 'c_3m_moc' in master_df.columns else master_df.get('px_last.1', 0.0), errors='coerce').fillna(0.0)

            metal_selection = st.selectbox("Select Target Base Metal to Analyze", ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"], key="tab1_metal_select")
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy().sort_values(by=col_date)
            
            if not df_metal.empty:
                df_metal['sma_20'] = df_metal['calc_cash_mid'].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal['calc_cash_mid'].rolling(window=50).mean()
                
                # --- METRICS ---
                latest = df_metal.iloc[-1]
                cols = st.columns(5)
                cols[0].metric("Cash Bid", f"${float(latest['calc_cash_bid']):,.2f}")
                cols[1].metric("Cash Ask", f"${float(latest['calc_cash_ask']):,.2f}")
                cols[2].metric("3M Bid", f"${float(latest['calc_3m_bid']):,.2f}")
                cols[3].metric("3M Ask", f"${float(latest['calc_3m_ask']):,.2f}")
                cols[4].metric("C-3M MOC", f"{float(latest['calc_c_3m_moc']):,.2f}")
                
                # --- CHART ---
                timeframe = st.radio("Select Chart Timeframe:", ["1W", "1M", "YTD", "1Y", "3Y", "5Y", "10Y", "ALL"], index=1, horizontal=True)
                max_d = df_metal[col_date].max()
                df_chart = df_metal.copy()
                if timeframe == "1W": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(weeks=1))]
                elif timeframe == "1M": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(days=30))]
                elif timeframe == "YTD": df_chart = df_chart[df_chart[col_date].dt.year == 2026]
                
                valid = df_chart[['calc_cash_mid']].dropna()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['calc_cash_mid'], name="Cash Mid"))
                fig.update_layout(height=400, template="plotly_white", yaxis=dict(range=[valid.min().min()*0.99, valid.max().max()*1.01], tickformat="$,.0f"))
                st.plotly_chart(fig, use_container_width=True)

                # --- LEDGERS ---
                with st.expander("🔍 View Raw Ingestion Ledger & Monthly Averages"):
                    st.markdown("### 📋 Raw Ingestion Ledger")
                    ledger = df_metal.sort_values(by=col_date, ascending=False).copy()
                    ledger['Date'] = ledger[col_date].dt.strftime('%Y-%m-%d')
                    st.dataframe(ledger, hide_index=True, use_container_width=True)
                    
                    st.markdown("### 📅 Monthly Average Pricing Analysis (2026)")
                    df_m = df_metal[df_metal[col_date].dt.year == 2026].copy()
                    df_m['Date_Obj'] = pd.to_datetime(df_m[col_date])
                    monthly = df_m.groupby(pd.Grouper(key='Date_Obj', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean().reset_index()
                    monthly = monthly.sort_values(by='Date_Obj', ascending=False)
                    monthly['Date'] = monthly['Date_Obj'].dt.strftime('%B %Y')
                    monthly = monthly.rename(columns={'calc_cash_ask': 'Avg 2RC Cash Ask', 'calc_3m_ask': 'Avg 2RC 3M Ask'})
                    st.dataframe(monthly[['Date', 'Avg 2RC Cash Ask', 'Avg 2RC 3M Ask']].style.format({"Avg 2RC Cash Ask": "${:,.2f}", "Avg 2RC 3M Ask": "${:,.2f}"}), hide_index=True, use_container_width=True)

        except Exception as e: st.error(f"❌ Error: {e}")

# TAB 2... (Keep your existing Tab 2 code)
