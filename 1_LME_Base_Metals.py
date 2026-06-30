import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="LME Base Metals Intelligence", layout="wide", page_icon="🏭")

st.title("🏭 London Metal Exchange (LME) Base Metals Panel")
st.caption("🌐 Global Cloud Engine — Native Cloud Sync Active")
st.markdown("---")

# --- NATIVE FILE RESOLVER LAYER ---
# Streamlit Cloud runs inside your repository folder structure.
# Because it already cloned your private repo, the file lives locally on the server!
FILE_PATH = "lme_master_data.csv"

try:
    # Read the data natively from the environment workspace
    if os.path.exists(FILE_PATH):
        master_df = pd.read_csv(FILE_PATH)
        
        METAL_OPTIONS = ["Copper", "Aluminium", "Tin", "Nickel", "Lead", "Zinc"]
        metal_selection = st.selectbox("Select Target Base Metal to Analyze", METAL_OPTIONS)
        
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
            col2.metric("Data Engine Status", "Cloud Active")
            col3.metric("Last Data Update", df_metal['date'].iloc[-1].strftime('%Y-%m-%d'))
            
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df_metal['date'], open=df_metal['open'], high=df_metal['high'], low=df_metal['low'], close=df_metal['close'], name=metal_selection
            )])
            fig_candle.update_layout(xaxis_rangeslider_visible=False, height=380, template="plotly_white", margin=dict(t=40, b=10))
            st.plotly_chart(fig_candle, use_container_width=True)
        else:
            st.warning("Data coordinates found, but target metal arrays are empty.")
    else:
        st.error(f"❌ File Allocation Error: '{FILE_PATH}' was not found in the root directory.")
        st.info("💡 Ensure your office script has run successfully and pushed the CSV file into your GitHub repository.")
except Exception as e:
    st.error(f"❌ Core Runtime Error: {e}")
