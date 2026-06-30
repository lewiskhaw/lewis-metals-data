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
