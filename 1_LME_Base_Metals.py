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
        url_main = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}?cb={int(datetime.now().timestamp())}"
        try:
            response = requests.get(url_main, headers=headers)
            if response.status_code == 200:
                master_df = pd.read_csv(StringIO(response.text))
        except Exception as e:
            st.error(f"❌ Connection Error: {e}")

    if master_df is not None:
        try:
            master_df.columns = [str(c).lower().strip() for c in master_df.columns]
            col_date, col_metal = 'date', 'metal'
            master_df[col_date] = pd.to_datetime(master_df[col_date], errors='coerce')
            master_df = master_df.dropna(subset=[col_date])
            
            # Calculations
            master_df['calc_cash_bid'] = pd.to_numeric(master_df.get('cash_bid', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_cash_ask'] = pd.to_numeric(master_df.get('cash_ask', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_cash_mid'] = (master_df['calc_cash_bid'] + master_df['calc_cash_ask']) / 2
            
            mb = master_df.get('px_bid.1', master_df.get('3m_bid', 0.0))
            ma = master_df.get('px_ask.1', master_df.get('3m_ask', 0.0))
            master_df['calc_3m_bid'] = pd.to_numeric(mb, errors='coerce').fillna(0.0)
            master_df['calc_3m_ask'] = pd.to_numeric(ma, errors='coerce').fillna(0.0)
            master_df['calc_3m_mid'] = (master_df['calc_3m_bid'] + master_df['calc_3m_ask']) / 2
            master_df['calc_c_3m_moc'] = pd.to_numeric(master_df.get('c_3m_moc', master_df.get('px_last.1', 0.0)), errors='coerce').fillna(0.0)

            metal_selection = st.selectbox("Select Target Base Metal to Analyze", ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"])
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy().sort_values(by=col_date)
            
            if not df_metal.empty:
                df_metal['sma_20'] = df_metal['calc_cash_mid'].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal['calc_cash_mid'].rolling(window=50).mean()
                
                # --- METRICS SECTION (Original format) ---
                latest = df_metal.iloc[-1]
                prior = df_metal.iloc[-2] if len(df_metal) > 1 else latest
                m_cols = st.columns(5)
                m_cols[0].metric(f"LME {metal_selection} 2RC Cash Bid", f"${float(latest['calc_cash_bid']):,.2f}", f"{float(latest['calc_cash_bid'])-float(prior['calc_cash_bid']):,.2f}")
                m_cols[1].metric(f"LME {metal_selection} 2RC Cash Ask", f"${float(latest['calc_cash_ask']):,.2f}", f"{float(latest['calc_cash_ask'])-float(prior['calc_cash_ask']):,.2f}")
                m_cols[2].metric(f"LME {metal_selection} 2RC 3M Bid", f"${float(latest['calc_3m_bid']):,.2f}", f"{float(latest['calc_3m_bid'])-float(prior['calc_3m_bid']):,.2f}")
                m_cols[3].metric(f"LME {metal_selection} 2RC 3M Ask", f"${float(latest['calc_3m_ask']):,.2f}", f"{float(latest['calc_3m_ask'])-float(prior['calc_3m_ask']):,.2f}")
                m_cols[4].metric(f"LME {metal_selection} C-3M MOC", f"{float(latest['calc_c_3m_moc']):,.2f}", f"{float(latest['calc_c_3m_moc'])-float(prior['calc_c_3m_moc']):,.2f}")
                
                st.markdown("---")
                
                # --- CHART ---
                timeframe = st.radio("Select Chart Timeframe:", ["1W", "1M", "YTD", "1Y", "3Y", "5Y", "10Y", "ALL"], index=1, horizontal=True)
                df_chart = df_metal.copy()
                max_d = df_metal[col_date].max()
                if timeframe == "1W": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(weeks=1))]
                elif timeframe == "1M": df_chart = df_chart[df_chart[col_date] >= (max_d - timedelta(days=30))]
                elif timeframe == "YTD": df_chart = df_chart[df_chart[col_date].dt.year == 2026]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['calc_cash_mid'], name="Cash Mid"))
                fig.update_layout(height=450, template="plotly_white", yaxis=dict(tickformat="$,.0f"))
                st.plotly_chart(fig, use_container_width=True)

                # --- LEDGER EXPANDER ---
                with st.expander("🔍 View Raw Ingestion Ledger & Monthly Averages"):
                    # RESTORED LEDGER
                    st.markdown("### 📋 Raw Ingestion Ledger")
                    ledger_df = df_metal.sort_values(by=col_date, ascending=False).copy()
                    ledger_df['ui_date'] = ledger_df[col_date].dt.strftime('%Y-%m-%d')
                    ledger_df['calc_c_3m_ask'] = ledger_df['calc_cash_ask'] - ledger_df['calc_3m_ask']
                    
                    rename_map = {
                        'ui_date': 'Date', 'metal': 'Metal',
                        'calc_cash_bid': '2RC Cash Bid', 'calc_cash_ask': '2RC Cash Ask', 'calc_cash_mid': '2RC Cash Mid',
                        'calc_3m_bid': '2RC 3M Bid', 'calc_3m_ask': '2RC 3M Ask', 'calc_3m_mid': '2RC 3M Mid',
                        'calc_c_3m_ask': '2RC C-3M Ask', 'calc_c_3m_moc': 'C-3M MOC', 'sma_20': 'SMA_20', 'sma_50': 'SMA_50'
                    }
                    display_df = ledger_df[[c for c in rename_map.keys() if c in ledger_df.columns]].rename(columns=rename_map)
                    
                    def apply_color(val):
                        if isinstance(val, (int, float)): return f'color: {"#dc3545" if val < 0 else "#000000"}; font-weight: 500;'
                        return ''
                    
                    styled = display_df.style.map(apply_color, subset=['2RC C-3M Ask', 'C-3M MOC']).format({col: "{:,.2f}" for col in display_df.columns if col not in ['Date', 'Metal']}, na_rep="-")
                    st.dataframe(styled, hide_index=True, use_container_width=True)
                    
                    # MONTHLY ANALYSIS
                    st.markdown("### 📅 Monthly Average Pricing Analysis (2026)")
                    df_2026 = df_metal[df_metal[col_date].dt.year == 2026].copy()
                    df_2026['Date_Obj'] = pd.to_datetime(df_2026[col_date])
                    monthly = df_2026.groupby(pd.Grouper(key='Date_Obj', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean().sort_index(ascending=False)
                    monthly['Date'] = monthly.index.strftime('%B %Y')
                    monthly = monthly.rename(columns={'calc_cash_ask': 'Avg 2RC Cash Ask', 'calc_3m_ask': 'Avg 2RC 3M Ask'})
                    st.dataframe(monthly[['Date', 'Avg 2RC Cash Ask', 'Avg 2RC 3M Ask']].style.format({"Avg 2RC Cash Ask": "${:,.2f}", "Avg 2RC 3M Ask": "${:,.2f}"}), hide_index=True, use_container_width=True)

        except Exception as e: st.error(f"❌ Error: {e}")

# ==============================================================================
# TAB 2: QUALITATIVE INTELLIGENCE INGESTION ENGINE
# ==============================================================================
with tab2:
    st.header("🔬 Multi-Agent Macro Case Studies & Briefings")
    CASE_STUDIES_DIR = "03_Case_Studies"
    if not os.path.exists(CASE_STUDIES_DIR):
        CASE_STUDIES_DIR = os.path.join("..", "03_Case_Studies")

    def get_available_case_studies():
        if not os.path.exists(CASE_STUDIES_DIR): return []
        return [f for f in os.listdir(CASE_STUDIES_DIR) if f.endswith(".md")]

    all_files = get_available_case_studies()

    if not all_files:
        st.info("🛰️ Awaiting initial automated synchronization stream from home desktop ingestion nodes...")
    else:
        display_options = {}
        for f in sorted(all_files, reverse=True):
            clean_name = f.replace(".md", "")
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', f)
            extracted_date = date_match.group(0) if date_match else today_str
            
            if "Global_Macro_Shift" in f:
                display_options[f] = f"🌐 Macro Shift Analysis: {extracted_date}"
            elif "Case_Study_Commodities" in f:
                display_options[f] = f"⚡ Commodity Case Study: {extracted_date}"
            elif "LME_Market_Briefing" in f:
                display_options[f] = f"📊 LME Pricing Brief: {extracted_date}"
            else:
                display_options[f] = f"📄 Data Asset: {clean_name}"

        selected_file = st.selectbox(
            "Select Target Intelligence Document to Load:", 
            options=list(display_options.keys()), 
            format_func=lambda x: display_options[x],
            key="tab2_brief_select"
        )
        file_path = os.path.join(CASE_STUDIES_DIR, selected_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f_content:
                raw_markdown = f_content.read()
            clean_markdown = re.sub(r'\[\[(.*?)\]\]', r'**\1**', raw_markdown)
            st.markdown("---")
            st.markdown(clean_markdown)
        except Exception as e:
            st.error(f"❌ Failed to parse selected case study: {e}")
