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
# TAB 1: QUANTITATIVE TRADING DESK METRICS (YOUR ORIGINAL LOGIC)
# ==============================================================================
with tab1:
    master_df = None
    
    # --- PHASE 1: PREFER LOCAL WORKSPACE LOAD (Fastest & Safest) ---
    # Since Streamlit clones your repo, check if the file is already sitting in the server root
    local_csv_path = "lme_master_data.csv"
    
    # If the app is inside a subfolder/pages directory, check one level up as well
    if not os.path.exists(local_csv_path):
        local_csv_path = os.path.join("..", "lme_master_data.csv")
        
    if os.path.exists(local_csv_path):
        try:
            master_df = pd.read_csv(local_csv_path)
            # st.caption("📡 Data Engine Mode: Native Workspace Sync")
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
                    # st.caption("📡 Data Engine Mode: GitHub API Fallback Sync")
                else:
                    st.error(f"⚠️ Failed to pull data from GitHub. HTTP Status Code: {response.status_code}")
                    st.info("Verify that lme_master_data.csv exists in your repository branch.")
            except Exception as e:
                st.error(f"❌ Remote Data Stream Error: {e}")

# --- PHASE 3: RENDER VISUALIZATION METRICS ---
    if master_df is not None:
        try:
            # Hardening: Force all column names to lowercase to eliminate case mismatches
            master_df.columns = [str(col).lower().strip() for col in master_df.columns]
            
            # Map columns to internal names based on what exists in the file
            # If 'close' isn't found, check if it's stored under 'current value' or 'price'
            col_map = {
                'metal': 'metal' if 'metal' in master_df.columns else master_df.columns[0],
                'date': 'date' if 'date' in master_df.columns else master_df.columns[1],
                'close': 'close' if 'close' in master_df.columns else ('current value' if 'current value' in master_df.columns else master_df.columns[2]),
                'open': 'open' if 'open' in master_df.columns else 'close',
                'high': 'high' if 'high' in master_df.columns else 'close',
                'low': 'low' if 'low' in master_df.columns else 'close'
            }
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            # Filter rows cleanly matching your target metal selection
            df_metal = master_df[master_df[col_map['metal']].astype(str).str.lower() == metal_selection.lower()].copy()
            
            df_metal[col_map['date']] = pd.to_datetime(df_metal[col_map['date']])
            df_metal = df_metal.sort_values(by=col_map['date']).reset_index(drop=True)
            
            if not df_metal.empty:
                current_price = float(df_metal[col_map['close']].iloc[-1])
                
                # Check if prior data rows exist for computing deltas, otherwise default to zero delta
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_map['close']].iloc[-2])
                    price_delta = current_price - prior_price
                    pct_delta = (price_delta / prior_price) * 100
                else:
                    price_delta, pct_delta = 0.0, 0.0
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"LME {metal_selection} Price", f"${current_price:,.2f}", f"{price_delta:+,.2f} ({pct_delta:+.2f}%)" if len(df_metal) > 1 else "0.00 (0.00%)")
                col2.metric("Data Engine Status", "Cloud Synced (Active)")
                col3.metric("Last Data Update", df_metal[col_map['date']].iloc[-1].strftime('%Y-%m-%d'))
                
                # Render Candlestick components
                fig_candle = go.Figure(data=[go.Candlestick(
                    x=df_metal[col_map['date']], 
                    open=df_metal[col_map['open']], 
                    high=df_metal[col_map['high']], 
                    low=df_metal[col_map['low']], 
                    close=df_metal[col_map['close']], 
                    name=metal_selection
                )])
                fig_candle.update_layout(xaxis_rangeslider_visible=False, height=380, template="plotly_white", margin=dict(t=40, b=10))
                st.plotly_chart(fig_candle, use_container_width=True)
            else:
                st.warning(f"Data file found, but requested asset class '{metal_selection}' returned empty rows.")
                st.caption(f"Available unique values in your file's metal column: {master_df[col_map['metal']].unique()}")
        except Exception as render_error:
            st.error(f"❌ Dashboard Rendering Anomaly: {render_error}")
            st.info("Debugging Data Schema View:")
            if master_df is not None:
                st.dataframe(master_df.head(2))

# ==============================================================================
# TAB 2: QUALITATIVE INTELLIGENCE INGESTION ENGINE (THE UPGRADE)
# ==============================================================================
with tab2:
    st.header("🔬 Multi-Agent Macro Case Studies")
    
    CASE_STUDIES_DIR = "03_Case_Studies"

    def get_available_case_studies():
        if not os.path.exists(CASE_STUDIES_DIR):
            return []
        files = [f for f in os.listdir(CASE_STUDIES_DIR) if f.endswith(".md")]
        return sorted(files, reverse=True)

    available_briefs = get_available_case_studies()

    if not available_briefs:
        st.info("🛰️ Awaiting initial automated synchronization stream from home desktop ingestion nodes...")
    else:
        selected_file = st.selectbox("Select Active Briefing File to Review:", available_briefs, key="tab2_brief_select")
        file_path = os.path.join(CASE_STUDIES_DIR, selected_file)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_markdown = f.read()
            clean_markdown = re.sub(r'\[\[(.*?)\]\]', r'**\1**', raw_markdown)
            st.markdown("---")
            st.markdown(clean_markdown)
        except Exception as e:
            st.error(f"❌ Failed to parse selected case study: {e}")
