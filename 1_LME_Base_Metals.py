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
                # Calculate indicators
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                # Extract terminal row metrics
                latest_row = df_metal.iloc[-1]
                current_cash_bid = float(latest_row['calc_cash_bid'])
                current_cash_ask = float(latest_row['calc_cash_ask'])
                current_3m_bid = float(latest_row['calc_3m_bid'])
                current_3m_ask = float(latest_row['calc_3m_ask'])
                current_c_3m_moc = float(latest_row['calc_c_3m_moc'])
                max_dataset_date = df_metal[col_date].max()
                
                # Metric display
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                m_col1.metric(f"LME {metal_selection} 2RC Cash Bid", f"${current_cash_bid:,.2f}")
                m_col2.metric(f"LME {metal_selection} 2RC Cash Ask", f"${current_cash_ask:,.2f}")
                m_col3.metric(f"LME {metal_selection} 2RC 3M Bid", f"${current_3m_bid:,.2f}")
                m_col4.metric(f"LME {metal_selection} 2RC 3M Ask", f"${current_3m_ask:,.2f}")
                m_col5.metric(f"LME {metal_selection} C-3M MOC", f"{current_c_3m_moc:+,.2f}")
                
                st.markdown("---")
                
                # --- LEDGER AND MONTHLY ANALYSIS ---
                with st.expander("🔍 View Raw Ingestion Ledger & Monthly Averages"):
                    # 1. Original Ledger
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
                    
                    styled_ledger = display_df.style.map(
                        lambda val: f'color: {"#dc3545" if val < 0 else "#000000"}; font-weight: 500;' if isinstance(val, (int, float)) else '', 
                        subset=['2RC C-3M Ask', 'C-3M MOC']
                    ).format({col: "{:,.2f}" for col in display_df.columns if col not in ['Date', 'Metal']})
                    
                    st.dataframe(styled_ledger, hide_index=True, use_container_width=True)
                    
                    # 2. Monthly Averages (Sorted latest on top)
                    st.markdown("### 📅 Monthly Average Pricing Analysis (2026)")
                    df_2026 = df_metal[df_metal[col_date].dt.year == 2026].copy()
                    df_2026['Date_Obj'] = pd.to_datetime(df_2026[col_date])
                    monthly_avg = df_2026.groupby(pd.Grouper(key='Date_Obj', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean().reset_index()
                    monthly_avg = monthly_avg.sort_values(by='Date_Obj', ascending=False)
                    monthly_avg['Date'] = monthly_avg['Date_Obj'].dt.strftime('%B %Y')
                    monthly_avg = monthly_avg.rename(columns={'calc_cash_ask': 'Avg 2RC Cash Ask', 'calc_3m_ask': 'Avg 2RC 3M Ask'})
                    
                    st.dataframe(monthly_avg[['Date', 'Avg 2RC Cash Ask', 'Avg 2RC 3M Ask']].style.format({"Avg 2RC Cash Ask": "${:,.2f}", "Avg 2RC 3M Ask": "${:,.2f}"}), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")

# TAB 2... (Keep your existing Tab 2 code)

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
