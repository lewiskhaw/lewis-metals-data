import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="LME Institutional Metals Panel", layout="wide", page_icon="🏭")

st.title("🏭 LME Institutional Base Metals Panel")
st.caption("🌐 Production Cloud Engine — Cash & 3-Month Prompt Pricing Diagnostics")
st.markdown("---")

FILE_PATH = "lme_master_data.csv"

if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    METAL_OPTIONS = sorted(df['metal'].unique())
    selected_metal = st.selectbox("Select Target Non-Ferrous Asset class:", METAL_OPTIONS)
    
    # Filter and calculate historical averages
    m_data = df[df['metal'] == selected_metal].sort_values(by='date').reset_index(drop=True)
    
    # Calculate Averages (30-Day and 90-Day Moving Averages on Cash Mid Price)
    m_data['cash_mid'] = (m_data['cash_bid'] + m_data['cash_ask']) / 2
    m_data['3m_mid'] = (m_data['3m_bid'] + m_data['3m_ask']) / 2
    m_data['30D_Avg'] = m_data['cash_mid'].rolling(window=30).mean()
    m_data['90D_Avg'] = m_data['cash_mid'].rolling(window=90).mean()
    
    # Current Coordinates Extract
    latest = m_data.iloc[-1]
    prior = m_data.iloc[-2]
    
    # Spread Diagnostics (Contango vs Backwardation)
    current_spread = latest['cash_mid'] - latest['3m_mid']
    spread_text = "Backwardation" if current_spread > 0 else "Contango"
    
    # --- UI SUMMARY TILES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Official Cash Mid Price", f"${latest['cash_mid']:,.2f}", f"{latest['cash_mid'] - prior['cash_mid']:+,.2f}")
    c2.metric("Official 3-Month Mid Price", f"${latest['3m_mid']:,.2f}", f"{latest['3m_mid'] - prior['3m_mid']:+,.2f}")
    c3.metric(f"Cash/3M Spread ({spread_text})", f"${abs(current_spread):,.2f}", f"Raw Value: {current_spread:+,.2f}")
    c4.metric("90-Day Cash Base Average", f"${latest['90D_Avg']:,.2f}")
    
    st.markdown("### 📊 Prompt Date Pricing Breakdown")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Cash Prompt Segment**")
        st.dataframe(pd.DataFrame({
            "Metric Parameter": ["Cash Bid", "Cash Ask", "30-Day Cash Average", "90-Day Cash Average"],
            "Current Value": [f"${latest['cash_bid']:,.2f}", f"${latest['cash_ask']:,.2f}", f"${latest['30D_Avg']:,.2f}", f"${latest['90D_Avg']:,.2f}"]
        }), use_container_width=True)
        
    with col_b:
        st.markdown("**3-Month Prompt Segment**")
        st.dataframe(pd.DataFrame({
            "Metric Parameter": ["3M Bid", "3M Ask", "Historical High (Period)", "Historical Low (Period)"],
            "Current Value": [f"${latest['3m_bid']:,.2f}", f"${latest['3m_ask']:,.2f}", f"${m_data['3m_mid'].max():,.2f}", f"${m_data['3m_mid'].min():,.2f}"]
        }), use_container_width=True)
        
    # --- GRAPHICAL TREND MATRIX ---
    st.markdown("### 📈 Historical Curve Diagnostics (Cash vs Averages)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m_data['date'], y=m_data['cash_mid'], name='Cash Mid Price', line=dict(color='#1f77b4', width=2)))
    fig.add_trace(go.Scatter(x=m_data['date'], y=m_data['3m_mid'], name='3M Mid Price', line=dict(color='#ff7f0e', width=1.5, dash='dash')))
    fig.add_trace(go.Scatter(x=m_data['date'], y=m_data['30D_Avg'], name='30-Day Moving Average', line=dict(color='#2ca02c', width=1.5)))
    fig.add_trace(go.Scatter(x=m_data['date'], y=m_data['90D_Avg'], name='90-Day Moving Average', line=dict(color='#d62728', width=1.5)))
    
    fig.update_layout(template="plotly_white", height=450, xaxis_title="Timeline", yaxis_title="USD / Metric Tonne", margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.error("❌ The backend data repository file has not arrived yet.")
