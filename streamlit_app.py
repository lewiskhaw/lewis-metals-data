import streamlit as st
import os
import re

st.set_page_config(page_title="Lewis Metals Intelligence Engine", page_icon="📊", layout="wide")

st.title("🖲️ Lewis Global Metals Data Engine")
st.caption("Synchronized Desk Dashboard — Hard Pricing Metrics & Multi-Agent Cognitive Synthesis")

# Create two distinct UI panel views across the layout header
tab1, tab2 = st.tabs(["📊 Live LME Metrics & Charts", "📂 Autonomous AI Case Studies"])

# ==============================================================================
# TAB 1: QUANTITATIVE TRADING DESK METRICS (YOUR ORIGINAL CODE)
# ==============================================================================
with tab1:
    st.header("Real-Time Price Matrices & Spread Curves")
    
    # 📊 PLACE YOUR EXISTING LME DATA AND PLOT CODES HERE
    # Drop your loops, pandas dataframes, plotly graphs, or file uploads right here.
    # It will render beautifully under this first tab section without interference.
    st.info("Your original pricing tickers, data frames, and interactive charts are live inside this tab.")


# ==============================================================================
# TAB 2: QUALITATIVE INTELLIGENCE INGESTION ENGINE (THE UPGRADE)
# ==============================================================================
with tab2:
    st.header("Multi-Agent Macro Case Studies")
    
    # Target directory folder where Git will drop your markdown files
    CASE_STUDIES_DIR = "03_Case_Studies"

    def get_available_case_studies():
        """Dynamically inventories all synchronized markdown briefs."""
        if not os.path.exists(CASE_STUDIES_DIR):
            return []
        # Fetch, filter, and reverse-sort files so the newest intelligence sits at the top
        files = [f for f in os.listdir(CASE_STUDIES_DIR) if f.endswith(".md")]
        return sorted(files, reverse=True)

    available_briefs = get_available_case_studies()

    if not available_briefs:
        st.info("Awaiting initial automated synchronization stream from home desktop ingestion nodes...")
    else:
        # Document selection dropbox right within Tab 2
        selected_file = st.selectbox("Select Active Briefing File to Read:", available_briefs)
        
        file_path = os.path.join(CASE_STUDIES_DIR, selected_file)
        
        with open(file_path, "r", encoding="utf-8") as f:
            raw_markdown = f.read()
            
        # Formatting Security Layer: Safely clean out internal Obsidian wiki-brackets [[ ]]
        clean_markdown = re.sub(r'\[\[(.*?)\]\]', r'**\1**', raw_markdown)
        
        # Render the synchronized workspace asset
        st.markdown("---")
        st.markdown(clean_markdown)
