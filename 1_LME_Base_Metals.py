import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
from io import StringIO
from datetime import datetime

# --- CONFIGURATION MATCHING YOUR REPO ---
GITHUB_USERNAME = "lewiskhaw"
GITHUB_REPO = "lewis-metals-data"
FILE_PATH = "lme_master_data.csv"

# Global date variable initialization to secure regex fallbacks
today_str = datetime.today().strftime('%Y-%m-%d')

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
    
    # --- PHASE 1: PREFER LOCAL WORKSPACE LOAD ---
    local_csv_path = "lme_master_data.csv"
    if not os.path.exists(local_csv_path):
        local_csv_path = os.path.join("..", "lme_master_data.csv")
        
    if os.path.exists(local_csv_path):
        try:
            master_df = pd.read_csv(local_csv_path)
        except Exception as e:
            st.warning(f"Failed to read local workspace CSV, attempting remote fallback: {e}")

    # --- PHASE 2: REMOTE URL FALLBACK ---
    if master_df is None:
        if "GITHUB_TOKEN" not in st.secrets:
            st.error("⚠️ GITHUB_TOKEN is missing from your Streamlit App Secrets.")
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
            except Exception as e:
                st.error(f"❌ Remote Data Stream Error: {e}")

    # --- PHASE 3: RENDER VISUALIZATION METRICS ---
    if master_df is not None:
        try:
            # Force columns to lowercase and remove trailing spaces
            master_df.columns = [str(col).lower().strip() for col in master_df.columns]
            
            col_date = 'date'
            col_metal = 'metal'
            
            # Convert strings to clean Datetime items FIRST
            master_df[col_date] = pd.to_datetime(master_df[col_date], format='mixed')
            
            # 🛑 VERIFIED DATABASE KEY MAPPING LAYER
            # Calculate Cash Mid Price dynamically
            if 'cash_bid' in master_df.columns and 'cash_ask' in master_df.columns:
                master_df['cash_mid'] = (master_df['cash_bid'] + master_df['cash_ask']) / 2
            
            # Calculate 3-Month Mid Price from fallback keys (px_bid.1 / px_ask.1)
            if 'px_bid.1' in master_df.columns and 'px_ask.1' in master_df.columns:
                master_df['3m_bid'] = master_df['px_bid.1']
                master_df['3m_ask'] = master_df['px_ask.1']
                master_df['3m_mid'] = (master_df['3m_bid'] + master_df['3m_ask']) / 2
                
            col_close = 'cash_mid' if 'cash_mid' in master_df.columns else master_df.columns[2]
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            # Filter rows for selected metal
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy()
            
            # Sort chronologically (oldest to newest) to completely fix the sawtooth chart pattern
            df_metal = df_metal.sort_values(by=col_date, ascending=True).reset_index(drop=True)
            
            if not df_metal.empty:
                # Calculate Technical Moving Average Indicators
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                current_price = float(df_metal[col_close].iloc[-1])
                
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_close].iloc[-2])
                    price_delta = current_price - prior_price
                    pct_delta = (price_delta / prior_price) * 100
                    delta_string = f"{price_delta:+,.2f} ({pct_delta:+.2f}%)"
                else:
                    delta_string = "0.00 (0.00%)"
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"LME {metal_selection} Cash Mid Price", f"${current_price:,.2f}", delta_string)
                col2.metric("Data Engine Status", "Cloud Synced (Active)")
                col3.metric("Last Data Update", df_metal[col_date].iloc[-1].strftime('%Y-%m-%d'))
                
                # --- LOAD TECHNICAL SIGNALS ---
                agent_signal, agent_reason, agent_color = "HOLD", "No active signal generated.", "gray"
                json_path = "03_Case_Studies/technical_signals.json"
                if not os.path.exists(json_path):
                    json_path = os.path.join("..", "03_Case_Studies", "technical_signals.json")
                
                signals_data = None
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as json_f:
                            signals_data = json.load(json_f)
                    except Exception: pass
                
                if signals_data is None and "GITHUB_TOKEN" in st.secrets:
                    try:
                        token = st.secrets["GITHUB_TOKEN"]
                        headers = {"Authorization": f"token {token}"}
                        json_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/03_Case_Studies/technical_signals.json"
                        json_res = requests.get(json_url, headers=headers)
                        if json_res.status_code == 200:
                            signals_data = json_res.json()
                    except Exception: pass

                if signals_data and metal_selection.lower() in signals_data:
                    m_sig = signals_data[metal_selection.lower()]
                    agent_signal = m_sig.get("signal", "HOLD")
                    agent_reason = m_sig.get("reason", "Consolidating within structural limits.")
                    agent_color = m_sig.get("color", "gray")

                st.info(f"🧠 **Technical Charting Agent Verdict:** `{agent_signal}` — {agent_reason}")

                # Build Main Line Chart
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal[col_close], name="Cash Mid Price", line=dict(color="#1f77b4", width=2)))
                fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal['sma_20'], name="20 DMA Overlay", line=dict(color="#2ca02c", width=1.2, dash='dot')))
                fig_line.add_trace(go.Scatter(x=df_metal[col_date], y=df_metal['sma_50'], name="50 DMA Overlay", line=dict(color="#d62728", width=1.2, dash='dot')))
                
                sig_bg = "rgba(40, 167, 69, 0.15)" if agent_color == "green" else ("rgba(220, 53, 69, 0.15)" if agent_color == "red" else "rgba(108, 117, 125, 0.15)")
                sig_border = "#28a745" if agent_color == "green" else ("#dc3545" if agent_color == "red" else "#6c7175")

                fig_line.add_annotation(
                    x=df_metal[col_date].iloc[-1], y=current_price,
                    text=f"🤖 AGENT OUTLOOK: {agent_signal}<br>${current_price:,.2f}",
                    showarrow=True, arrowhead=2, arrowcolor=sig_border, arrowsize=1, arrowwidth=2,
                    ax=-90, ay=-50, bordercolor=sig_border, borderwidth=2, borderpad=6, bgcolor=sig_bg,
                    opacity=0.95, font=dict(color="black", size=12)
                )
                
                fig_line.update_layout(
                    height=500, template="plotly_white", margin=dict(t=20, b=10, l=10, r=10),
                    xaxis_title="Timeline", yaxis_title="USD / Metric Tonne",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_line, use_container_width=True)
                
                # ==============================================================================
                # 🛠️ HARDENED 10-COLUMN INGESTION LEDGER DATA BLOCK
                # ==============================================================================
                with st.expander("🔍 View Raw Ingestion Ledger Data"):
                    # 1. Reverse sort so the newest data point stays at the top of the grid view
                    ledger_df = df_metal.sort_values(by=col_date, ascending=False).copy()
                    
                    # 2. Format timestamps to clean calendar strings
                    ledger_df['formatted_date'] = ledger_df[col_date].dt.strftime('%Y-%m-%d')
                    
                    # 3. Requesting your exact custom column sequence structure
                    desired_columns = [
                        'formatted_date', 'metal', 
                        'cash_bid', 'cash_ask', 'cash_mid', 
                        '3m_bid', '3m_ask', '3m_mid', 
                        'sma_20', 'sma_50'
                    ]
                    
                    # Filter down safely to exactly what exists in our memory structure
                    available_cols = [col for col in desired_columns if col in ledger_df.columns]
                    ledger_df = ledger_df[available_cols]
                    
                    # 4. Safe UI column renaming map
                    rename_map = {
                        'formatted_date': 'Date',
                        'metal': 'Metal',
                        'cash_bid': 'Cash Bid',
                        'cash_ask': 'Cash Ask',
                        'cash_mid': 'Cash Mid',
                        '3m_bid': '3M Bid',
                        '3m_ask': '3M Ask',
                        '3m_mid': '3M Mid',
                        'sma_20': 'SMA_20',
                        'sma_50': 'SMA_50'
                    }
                    current_rename = {k: v for k, v in rename_map.items() if k in ledger_df.columns}
                    ledger_df = ledger_df.rename(columns=current_rename)
                    
                    # 5. Display the clean data grid frame without index numbers
                    st.dataframe(ledger_df, hide_index=True, use_container_width=True)
                    
            else:
                st.warning(f"Data file found, but requested asset class '{metal_selection}' returned empty rows.")
        except Exception as render_error:
            st.error(f"❌ Dashboard Rendering Anomaly: {render_error}")

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
