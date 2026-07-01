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
                # Calculate indicators globally over full database timeframe first
                df_metal['sma_20'] = df_metal[col_close].rolling(window=20).mean()
                df_metal['sma_50'] = df_metal[col_close].rolling(window=50).mean()

                # Extract terminal row metrics cleanly
                latest_row = df_metal.iloc[-1]
                current_cash_bid = float(latest_row['calc_cash_bid'])
                current_cash_ask = float(latest_row['calc_cash_ask'])
                current_3m_bid = float(latest_row['calc_3m_bid'])
                current_3m_ask = float(latest_row['calc_3m_ask'])
                current_c_3m_moc = float(latest_row['calc_c_3m_moc'])
                current_cash_mid = float(latest_row['calc_cash_mid'])
                max_dataset_date = df_metal[col_date].max()
                
                # 🎯 COMPUTE DYNAMIC METRIC VARIANCE DELTAS
                cb_delta, ca_delta, mb_delta, ma_delta, moc_delta_str = "0.00 (0.00%)", "0.00 (0.00%)", "0.00 (0.00%)", "0.00 (0.00%)", "0.00"
                moc_is_positive_change = True
                
                if len(df_metal) > 1:
                    prior_row = df_metal.iloc[-2]
                    
                    # Cash Bid
                    p_cb = float(prior_row['calc_cash_bid'])
                    d_cb = current_cash_bid - p_cb
                    cb_delta = f"{d_cb:+,.2f} ({(d_cb/p_cb)*100:+.2f}%)" if p_cb != 0 else "0.00 (0.00%)"
                    
                    # Cash Ask
                    p_ca = float(prior_row['calc_cash_ask'])
                    d_ca = current_cash_ask - p_ca
                    ca_delta = f"{d_ca:+,.2f} ({(d_ca/p_ca)*100:+.2f}%)" if p_ca != 0 else "0.00 (0.00%)"
                    
                    # 3M Bid
                    p_mb = float(prior_row['calc_3m_bid'])
                    d_mb = current_3m_bid - p_mb
                    mb_delta = f"{d_mb:+,.2f} ({(d_mb/p_mb)*100:+.2f}%)" if p_mb != 0 else "0.00 (0.00%)"
                    
                    # 3M Ask
                    p_ma = float(prior_row['calc_3m_ask'])
                    d_ma = current_3m_ask - p_ma
                    ma_delta = f"{d_ma:+,.2f} ({(d_ma/p_ma)*100:+.2f}%)" if p_ma != 0 else "0.00 (0.00%)"

                    # Centralized Spread Ingestion Tracking (C-3M MOC Delta)
                    p_moc = float(prior_row['calc_c_3m_moc'])
                    d_moc = current_c_3m_moc - p_moc
                    moc_is_positive_change = (d_moc >= 0)
                    pct_moc = (d_moc / abs(p_moc)) * 100 if p_moc != 0 else 0.0
                    moc_delta_str = f"{d_moc:+,.2f} ({pct_moc:+.2f}%)"

                # 📊 PRODUCTION 5-COLUMN REBRANDED DISPLAY MATRIX
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                
                m_col1.metric(f"LME {metal_selection} 2RC Cash Bid", f"${current_cash_bid:,.2f}", cb_delta)
                m_col2.metric(f"LME {metal_selection} 2RC Cash Ask", f"${current_cash_ask:,.2f}", ca_delta)
                m_col3.metric(f"LME {metal_selection} 2RC 3M Bid", f"${current_3m_bid:,.2f}", mb_delta)
                m_col4.metric(f"LME {metal_selection} 2RC 3M Ask", f"${current_3m_ask:,.2f}", ma_delta)
                
                # 🎨 TRADING TERMINAL CONDITION SPEC LABELS FOR MOC SPREAD
                structure_label = "Contango" if current_c_3m_moc < 0 else "Backwardation"
                moc_color = "#dc3545" if current_c_3m_moc < 0 else "#000000"
                
                delta_bg = "rgba(40, 167, 69, 0.12)" if moc_is_positive_change else "rgba(220, 53, 69, 0.12)"
                delta_text_color = "#28a745" if moc_is_positive_change else "#dc3545"
                delta_arrow = "↑" if moc_is_positive_change else "↓"

                with m_col5:
                    st.markdown(
                        f"""
                        <div style='line-height: 1.2;'>
                            <p style='font-size: 14px; color: rgb(49, 51, 63); margin-bottom: 0px;'>LME {metal_selection} C-3M MOC</p>
                            <p style='font-size: 36px; font-weight: 600; color: {moc_color}; margin-top: 4px; margin-bottom: 4px;'>{current_c_3m_moc:+,.2f}</p>
                            <div style='display: inline-flex; align-items: center; background-color: {delta_bg}; color: {delta_text_color}; padding: 2px 8px; border-radius: 4px; font-size: 14px; font-weight: 500; margin-bottom: 8px;'>
                                {delta_arrow} {moc_delta_str}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    st.caption(f"📊 Structure: **{structure_label}**")

                st.markdown(f"**Data Engine Status:** `Cloud Synced (Active)` &nbsp;|&nbsp; **Last Data Update:** `{max_dataset_date.strftime('%Y-%m-%d')}`")
                st.markdown("---")
                
                # --- LOAD AGENT VERDICTS ---
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

                # 🚀 HARD SERVER-SIDE TIMEFRAME FILTERS
                st.write("")
                timeframe = st.radio(
                    "Select Chart Timeframe:",
                    options=["1W", "1M", "YTD", "1Y", "3Y", "5Y", "10Y", "ALL"],
                    index=1,  # Default fallback focus window to 1M
                    horizontal=True
                )

                # Execute explicit dataset window slicing based on the choice
                df_chart = df_metal.copy()
                if timeframe == "1W":
                    cutoff = max_dataset_date - timedelta(weeks=1)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "1M":
                    cutoff = max_dataset_date - timedelta(days=30)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "YTD":
                    cutoff = datetime(max_dataset_date.year, 1, 1)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "1Y":
                    cutoff = max_dataset_date - timedelta(days=365)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "3Y":
                    cutoff = max_dataset_date - timedelta(days=365 * 3)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "5Y":
                    cutoff = max_dataset_date - timedelta(days=365 * 5)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]
                elif timeframe == "10Y":
                    cutoff = max_dataset_date - timedelta(days=365 * 10)
                    df_chart = df_chart[df_chart[col_date] >= cutoff]

                df_chart = df_chart.reset_index(drop=True)

                # 📊 HIGH-SPEC FINANCIAL GRAPH ENGINE WITH EXPONENTIALLY CLAUSTROPHOBIC BINDING BOUNDS
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart[col_close], name="Cash Mid Price", line=dict(color="#1f77b4", width=2)))
                fig_line.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['sma_20'], name="20 DMA Overlay", line=dict(color="#2ca02c", width=1.2, dash='dot')))
                fig_line.add_trace(go.Scatter(x=df_chart[col_date], y=df_chart['sma_50'], name="50 DMA Overlay", line=dict(color="#d62728", width=1.2, dash='dot')))
                
                chart_title_text = f"LME {metal_selection} {timeframe} Trend Tracker | Outlook: <b>{agent_signal}</b>"

                # Drops missing NaN records completely for perfect bounding
                valid_prices = df_chart[[col_close, 'sma_20', 'sma_50']].dropna()
                if not valid_prices.empty:
                    y_min = float(valid_prices.min().min()) * 0.99  # Clean 1% terminal floor pad
                    y_max = float(valid_prices.max().max()) * 1.01  # Clean 1% terminal ceiling pad
                else:
                    y_min, y_max = None, None

                fig_line.update_layout(
                    title=dict(text=chart_title_text, font=dict(size=14, color="black")),
                    height=520, template="plotly_white", margin=dict(t=40, b=10, l=10, r=10),
                    xaxis_title="Timeline", yaxis_title="USD / Metric Tonne",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(
                        range=[y_min, y_max] if y_min is not None else None,
                        autorange=False if y_min is not None else True,
                        fixedrange=False,
                        # 🎯 PREMIUM TEXT FORMATTING OVERRIDE: Formats values into pure Bloomberg currency numbers
                        tickformat="$,.0f"
                    ),
                    xaxis=dict(
                        range=[df_chart[col_date].min(), max_dataset_date],
                        type="date"
                    )
                )
                
                st.plotly_chart(fig_line, use_container_width=True)
                
                # ==============================================================================
                # 📊 PRODUCTION DATA DISPLAY LEDGER WITH STYLE ENGINES
                # ==============================================================================
                # 🔍 VIEW RAW INGESTION LEDGER & MONTHLY AVERAGES
                with st.expander("🔍 View Raw Ingestion Ledger Data"):
                    
                    # 1. RENDER ORIGINAL LEDGER (Original code preserved)
                    ledger_df = df_metal.sort_values(by=col_date, ascending=False).copy()
                    ledger_df['ui_date'] = ledger_df[col_date].dt.strftime('%Y-%m-%d')
                    ledger_df['calc_c_3m_ask'] = ledger_df['calc_cash_ask'] - ledger_df['calc_3m_ask']
                    
                    desired_columns = [
                        'ui_date', 'metal', 
                        'calc_cash_bid', 'calc_cash_ask', 'calc_cash_mid', 
                        'calc_3m_bid', 'calc_3m_ask', 'calc_3m_mid', 
                        'calc_c_3m_ask', 'calc_c_3m_moc', 'sma_20', 'sma_50'
                    ]
                    available_cols = [col for col in desired_columns if col in ledger_df.columns]
                    ledger_df = ledger_df[available_cols]
                    
                    rename_map = {
                        'ui_date': 'Date', 'metal': 'Metal',
                        'calc_cash_bid': '2RC Cash Bid', 'calc_cash_ask': '2RC Cash Ask', 'calc_cash_mid': '2RC Cash Mid',
                        'calc_3m_bid': '2RC 3M Bid', 'calc_3m_ask': '2RC 3M Ask', 'calc_3m_mid': '2RC 3M Mid',
                        'calc_c_3m_ask': '2RC C-3M Ask', 'calc_c_3m_moc': 'C-3M MOC', 'sma_20': 'SMA_20', 'sma_50': 'SMA_50'
                    }
                    ledger_df = ledger_df.rename(columns=rename_map)
                    
                    def apply_color_mapping(val):
                        if isinstance(val, (int, float)):
                            color = '#dc3545' if val < 0 else '#000000'
                            return f'color: {color}; font-weight: 500;'
                        return ''
                    
                    styled_ledger = ledger_df.style.map(apply_color_mapping, subset=['2RC C-3M Ask', 'C-3M MOC']).format({
                        col: "{:,.2f}" for col in ledger_df.columns if col not in ['Date', 'Metal']
                    }, na_rep="-")
                    
                    st.dataframe(styled_ledger, hide_index=True, use_container_width=True)
                    
                    # 2. NEW MONTHLY AVERAGES SECTION (Added below without affecting above)
                    st.markdown("### 📅 Monthly Average Pricing Analysis (2026)")
                    
                    # Create monthly slice
                    df_m = df_metal[df_metal[col_date].dt.year == 2026].copy()
                    df_m['Date_Obj'] = pd.to_datetime(df_m[col_date])
                    
                    # Grouping
                    monthly_avg = df_m.groupby(pd.Grouper(key='Date_Obj', freq='ME'))[['calc_cash_ask', 'calc_3m_ask']].mean().reset_index()
                    
                    # Sorting latest at the top
                    monthly_avg = monthly_avg.sort_values(by='Date_Obj', ascending=False)
                    
                    # Formatting
                    monthly_avg['Date'] = monthly_avg['Date_Obj'].dt.strftime('%B %Y')
                    monthly_avg = monthly_avg.rename(columns={'calc_cash_ask': 'Avg 2RC Cash Ask', 'calc_3m_ask': 'Avg 2RC 3M Ask'})
                    
                    # Table Output
                    st.dataframe(monthly_avg[['Date', 'Avg 2RC Cash Ask', 'Avg 2RC 3M Ask']].style.format({
                        "Avg 2RC Cash Ask": "${:,.2f}", 
                        "Avg 2RC 3M Ask": "${:,.2f}"
                    }), hide_index=True, use_container_width=True)
                    
                    # Business Rebranding Definitions
                    rename_map = {
                        'ui_date': 'Date', 'metal': 'Metal',
                        'calc_cash_bid': '2RC Cash Bid', 'calc_cash_ask': '2RC Cash Ask', 'calc_cash_mid': '2RC Cash Mid',
                        'calc_3m_bid': '2RC 3M Bid', 'calc_3m_ask': '2RC 3M Ask', 'calc_3m_mid': '2RC 3M Mid',
                        'calc_c_3m_ask': '2RC C-3M Ask', 'calc_c_3m_moc': 'C-3M MOC', 'sma_20': 'SMA_20', 'sma_50': 'SMA_50'
                    }
                    current_rename = {k: v for k, v in rename_map.items() if k in ledger_df.columns}
                    ledger_df = ledger_df.rename(columns=current_rename)
                    
                    # CSS STYLING ENGINE FOR CONDITIONAL COLOR MAPPING
                    def apply_color_mapping(val):
                        if isinstance(val, (int, float)):
                            color = '#dc3545' if val < 0 else '#000000'
                            return f'color: {color}; font-weight: 500;'
                        return ''
                    
                    styled_ledger = ledger_df.style.map(apply_color_mapping, subset=['2RC C-3M Ask', 'C-3M MOC'])
                    
                    # Round formatting parameters for ledger cleanliness
                    styled_ledger = styled_ledger.format({
                        '2RC Cash Bid': '{:,.2f}', '2RC Cash Ask': '{:,.2f}', '2RC Cash Mid': '{:,.2f}',
                        '2RC 3M Bid': '{:,.2f}', '2RC 3M Ask': '{:,.2f}', '2RC 3M Mid': '{:,.2f}',
                        '2RC C-3M Ask': '{:,.2f}', 'C-3M MOC': '{:,.2f}', 'SMA_20': '{:,.2f}', 'SMA_50': '{:,.2f}'
                    }, na_rep="-")
                    
                    st.dataframe(styled_ledger, hide_index=True, use_container_width=True)
                    
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
