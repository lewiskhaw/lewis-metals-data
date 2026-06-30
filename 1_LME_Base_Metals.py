import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
from io import StringIO

# --- CONFIGURATION MATCHING YOUR REPO ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"

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
            
            # Map columns to calculate a synthetic mid-price from prompt structures
            if 'cash_bid' in master_df.columns and 'cash_ask' in master_df.columns:
                master_df['cash_mid'] = (master_df['cash_bid'] + master_df['cash_ask']) / 2
                col_close = 'cash_mid'
            else:
                col_close = master_df.columns[2] # Fallback to 3rd column if schema shifts
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            # Filter rows matching the selected metal
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy()
            
            df_metal[col_date] = pd.to_datetime(df_metal[col_date])
            df_metal = df_metal.sort_values(by=col_date).reset_index(drop=True)
            
            if not df_metal.empty:
                current_price = float(df_metal[col_close].iloc[-1])
                
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_close].iloc[-2])
                    price_delta = current_price - prior_price
                    pct_delta = (price_delta / prior_price) * 100
                else:
                    price_delta, pct_delta = 0.0, 0.0
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"LME {metal_selection} Cash Mid Price", f"${current_price:,.2f}", f"{price_delta:+,.2f} ({pct_delta:+.2f}%)" if len(df_metal) > 1 else "0.00 (0.00%)")
                col2.metric("Data Engine Status", "Cloud Synced (Active)")
                col3.metric("Last Data Update", df_metal[col_date].iloc[-1].strftime('%Y-%m-%d'))
                
                # Multi-Curve Scatter Plot Tracking Prompt Date Spreads
                fig_line = go.Figure()
                
                if 'cash_bid' in df_metal.columns:
                    fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal['cash_bid'], name="Cash Bid", line=dict(color="#1f77b4", width=2)))
                
                if 'cash_ask' in df_metal.columns:
                    fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal['cash_ask'], name="Cash Ask", line=dict(color="#aec7e8", width=1.5, dash='dash')))
                
                if '3m_bid' in df_metal.columns:
                    fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal['3m_bid'], name="3M Bid", line=dict(color="#ff7f0e", width=2)))
                
                fig_line.update_layout(
                    height=450, 
                    template="plotly_white", 
                    margin=dict(t=40, b=10, l=10, r=10),
                    xaxis_title="Timeline",
                    yaxis_title="USD / Metric Tonne",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_line, use_container_width=True)
                
                with st.expander("🔍 View Raw Ingestion Ledger Data"):
                    st.dataframe(df_metal.tail(10))
            else:
                st.warning(f"Data file found, but requested asset class '{metal_selection}' returned empty rows.")
        except Exception as render_error:
            st.error(f"❌ Dashboard Rendering Anomaly: {render_error}")

# ==============================================================================
# TAB 2: QUALITATIVE INTELLIGENCE INGESTION ENGINE (THE UPGRADE)
# ==============================================================================
with tab2:
    st.header("🔬 Multi-Agent Macro Case Studies & Briefings")
    
    CASE_STUDIES_DIR = "03_Case_Studies"
    
    if not os.path.exists(CASE_STUDIES_DIR):
        CASE_STUDIES_DIR = os.path.join("..", "03_Case_Studies")

    def get_available_case_studies():
        if not os.path.exists(CASE_STUDIES_DIR):
            return []
        return [f for f in os.listdir(CASE_STUDIES_DIR) if f.endswith(".md")]

    all_files = get_available_case_studies()

    if not all_files:
        st.info("🛰️ Awaiting initial automated synchronization stream from home desktop ingestion nodes...")
    else:
        display_options = {}
        for f in sorted(all_files, reverse=True):
            clean_name = f.replace(".md", "")
            
            # Extract date safely using a 10-character boundary matching regular expression pattern
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', f)
            extracted_date = date_match.group(0) if date_match else today_str
            
            # Resilient label distribution matrix
            if "Global_Macro_Shift" in f:
                display_options[f] = f"🌐 Macro Shift Analysis: {extracted_date}"
            elif "Case_Study_Commodities" in f:
                display_options[f] = f"⚡ Commodity Case Study: {extracted_date}"
            elif "LME_Market_Briefing" in f:
                display_options[f] = f"📊 LME Pricing Brief: {extracted_date}"
            else:
                display_options[f] = f"📄 Data Asset: {clean_name}"

        # Dropdown selection menu displaying the beautiful labels
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
