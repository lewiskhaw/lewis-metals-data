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
            
            # Calculations
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
                df_metal['sma_20'] = df_metal['calc_cash_mid'].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal['calc_cash_mid'].rolling(window=50).mean()
                
                # Metrics Section
                latest_row = df_metal.iloc[-1]
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                m_col1.metric("LME Copper 2RC Cash Bid", f"${float(latest_row['calc_cash_bid']):,.2f}")
                m_col2.metric("LME Copper 2RC Cash Ask", f"${float(latest_row['calc_cash_ask']):,.2f}")
                m_col3.metric("LME Copper 2RC 3M Bid", f"${float(latest_row['calc_3m_bid']):,.2f}")
                m_col4.metric("LME Copper 2RC 3M Ask", f"${float(latest_row['calc_3m_ask']):,.2f}")
                m_col5.metric("LME Copper C-3M MOC", f"{float(latest_row['calc_c_3m_moc']):,.2f}")
                
                # Charting
                timeframe = st.radio("Select Chart Timeframe:", ["1W", "1M", "YTD", "1Y", "3Y", "5Y", "10Y", "ALL"], index=1, horizontal=True)
                max_d = df_metal[col_date].max()
                
                df_chart = df_metal.copy()
                if timeframe == "1W": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(weeks=1))]
                elif timeframe == "1M": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(days=30))]
                elif timeframe == "YTD": df_chart = df_chart[df_chart[col_date].dt.year == 2026]
                
                # Tight Y-Axis Autoscaling
                valid_data = df_chart[['calc_cash_mid', 'sma_20', 'sma_50']].dropna()
                y_min = float(valid_data.min().min()) * 0.995 if not valid_data.empty else None
                y_max = float(valid_data.max().max()) * 1.005 if not valid_data.empty else None

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['calc_cash_mid'], name="Cash Mid"))
                fig.update_layout(height=500, template="plotly_white", yaxis=dict(range=[y_min, y_max], tickformat="$,.0f"))
                st.plotly_chart(fig, use_container_width=True)

                # Ledgers & Monthly Analysis
                with st.expander("🔍 View Raw Ingestion Ledger & Monthly Averages"):
                    st.dataframe(df_metal.sort_values(by=col_date, ascending=False), use_container_width=True)
                    
                    st.markdown("### 📅 Monthly Average Pricing Analysis (2026)")
                    df_2026 = df_metal[df_metal[col_date].dt.year == 2026].copy()
                    df_2026['Date'] = pd.to_datetime(df_2026[col_date])
                    monthly_avg = df_2026.groupby(pd.Grouper(key='Date', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean().reset_index()
                    monthly_avg['Date'] = monthly_avg['Date'].dt.strftime('%B %Y')
                    monthly_avg = monthly_avg.rename(columns={'calc_cash_ask': 'Avg 2RC Cash Ask', 'calc_3m_ask': 'Avg 2RC 3M Ask'})
                    st.dataframe(monthly_avg.style.format({"Avg 2RC Cash Ask": "${:,.2f}", "Avg 2RC 3M Ask": "${:,.2f}"}), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Dashboard Error: {e}")

# TAB 2... (Keep your existing Tab 2 code)
