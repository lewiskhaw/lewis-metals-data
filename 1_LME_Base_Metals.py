import os
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import re
import json
from io import StringIO
from datetime import datetime

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
    
    # 🛑 STRUCTURAL UPGRADE: Force remote pull directly from GitHub API to bypass old local workspace file conflicts
    if "GITHUB_TOKEN" not in st.secrets:
        st.error("⚠️ GITHUB_TOKEN is missing from your Streamlit App Secrets.")
        st.info("Please go to your Streamlit Cloud Dashboard -> App Settings -> Secrets, and add your token.")
    else:
        token = st.secrets["GITHUB_TOKEN"]
        headers = {"Authorization": f"token {token}"}
        url_main = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/{FILE_PATH}"
        url_master = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/master/{FILE_PATH}"

        try:
            # Append a cache-busting timestamp to the URL parameters to force GitHub to serve the absolute freshest data row commit
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
            # Standardize columns to lowercase and strip out spaces
            master_df.columns = [str(c).lower().strip() for c in master_df.columns]
            
            col_date = 'date'
            col_metal = 'metal'
            
            # Form chronological Datetime objects cleanly
            master_df[col_date] = pd.to_datetime(master_df[col_date], dayfirst=True, errors='coerce')
            master_df = master_df.dropna(subset=[col_date])
            
            # 🎯 DIRECT KEY EXTRACTOR (Bypasses traditional fallback errors)
            master_df['calc_cash_bid'] = pd.to_numeric(master_df.get('cash_bid', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_cash_ask'] = pd.to_numeric(master_df.get('cash_ask', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_cash_mid'] = (master_df['calc_cash_bid'] + master_df['calc_cash_ask']) / 2
            
            master_df['calc_3m_bid'] = pd.to_numeric(master_df.get('3m_bid', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_3m_ask'] = pd.to_numeric(master_df.get('3m_ask', 0.0), errors='coerce').fillna(0.0)
            master_df['calc_3m_mid'] = (master_df['calc_3m_bid'] + master_df['calc_3m_ask']) / 2

            col_close = 'calc_cash_mid'
            
            METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
            metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS, key="tab1_metal_select")
            
            df_metal = master_df[master_df[col_metal].astype(str).str.lower() == metal_selection.lower()].copy()
            df_metal = df_metal.sort_values(by=col_date, ascending=True).reset_index(drop=True)
            
            if not df_metal.empty:
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                current_price = float(df_metal[col_close].iloc[-1])
                
                if len(df_metal) > 1:
                    prior_price = float(df_metal[col_close].iloc[-2])
                    price_delta = current_price - prior_price
                    if prior_price != 0:
                        pct_delta = (price_delta / prior_price) * 100
                        delta_string = f"{price_delta:+,.2f} ({pct_delta:+.2f}%)"
                    else:
                        delta_string = f"{price_delta:+,.2f} (0.00%)"
                else:
                    delta_string = "0.00 (0.00%)"
                
                col1, col2, col3 = st.columns(3)
                col1.metric(f"LME {metal_selection} Cash Mid Price", f"${current_price:,.2f}", delta_string)
                col2.metric("Data Engine Status", "Cloud Synced (Active)")
                col3.metric("Last Data Update", df_metal[col_date].iloc[-1].strftime('%Y-%m-%d'))
                
                # --- LOAD AGENT SIGNAL VERDICT ---
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

                # Plot Main Interactive Graph Layout
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
                # 📊 PRODUCTION 10-COLUMN DISPLAY LEDGER
                # ==============================================================================
                with st.expander("🔍 View Raw Ingestion Ledger Data"):
                    ledger_df = df_metal.sort_values(by=col_date, ascending=False).copy()
                    
                    ledger_df['ui_date'] = ledger_df[col_date].dt.strftime('%Y-%m-%d')
                    
                    desired_columns = [
                        'ui_date', 'metal', 
                        'calc_cash_bid', 'calc_cash_ask', 'calc_cash_mid', 
                        'calc_3m_bid', 'calc_3m_ask', 'calc_3m_mid', 
                        'sma_20', 'sma_50'
                    ]
                    
                    available_cols = [col for col in desired_columns if col in ledger_df.columns]
                    ledger_df = ledger_df[available_cols]
                    
                    rename_map = {
                        'ui_date': 'Date', 'metal': 'Metal',
                        'calc_cash_bid': 'Cash Bid', 'calc_cash_ask': 'Cash Ask', 'calc_cash_mid': 'Cash Mid',
                        'calc_3m_bid': '3M Bid', 'calc_3m_ask': '3M Ask', 'calc_3m_mid': '3M Mid',
                        'sma_20': 'SMA_20', 'sma_50': 'SMA_50'
                    }
                    current_rename = {k: v for k, v in rename_map.items() if k in ledger_df.columns}
                    ledger_df = ledger_df.rename(columns=current_rename)
                    
                    st.dataframe(ledger_df, hide_index=True, use_container_width=True)
                    
            else:
                st.warning("Data file successfully fetched from cloud, but requested asset class returned empty rows.")
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
