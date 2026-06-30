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
                metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
                
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
        except Exception as e:
            st.error(f"❌ Data Stream Error: {e}")

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
