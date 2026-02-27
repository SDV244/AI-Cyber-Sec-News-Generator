import os
import streamlit as st
from datetime import datetime
import threading

from config import logger, TIMEZONE
import scraper
import ai_synthesizer
import pdf_generator
import whatsapp_formatter
from utils import deduplicate_items, get_week_label

# Must be the first Streamlit command
st.set_page_config(
    page_title="Cyber Intel Weekly",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS (APPLE-LIKE AESTHETIC) ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FBFBFD; /* Apple Light Gray */
        color: #1D1D1F; /* Apple Dark Gray */
    }
    
    .stApp {
        background-color: #FBFBFD;
    }

    /* Top Header */
    header {
        background-color: rgba(251, 251, 253, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }

    /* Cards */
    .st-emotion-cache-12w0qpk, div[data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #0071E3; /* Apple Blue */
        color: white;
        border-radius: 980px; /* Pill shape */
        padding: 12px 24px;
        font-weight: 500;
        border: none;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0, 113, 227, 0.2);
    }
    
    .stButton>button:hover {
        background-color: #0077ED;
        box-shadow: 0 6px 12px rgba(0, 113, 227, 0.3);
        transform: scale(1.02);
    }
    
    /* Config Inputs */
    .stTextInput>div>div>input {
        border-radius: 12px;
        border: 1px solid #d2d2d7;
        background-color: #FFFFFF;
        padding: 12px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #0071E3;
        box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #E3E3E8;
        padding: 4px;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 32px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #1D1D1F;
        font-size: 14px;
        font-weight: 500;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF;
        color: #1D1D1F;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# === APP LOGIC ===

def load_env_file():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_env_file(content):
    env_path = ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_newsletter():
    with st.spinner("🚀 Initializing intelligence collection pipeline..."):
        try:
            # Step 1
            st.info("📡 Scraping threat intelligence sources...")
            raw_items = scraper.collect_all_sources()
            all_items = deduplicate_items(raw_items)
            
            if len(all_items) == 0:
                st.warning("⚠️ No intel found for the current week!")
                return
            
            # Step 2
            st.info(f"🧠 Synthesizing {len(all_items)} articles with Gemini AI...")
            newsletter_data = ai_synthesizer.synthesize(all_items)
            
            # Step 3
            st.info("📄 Compiling Executive PDF and WhatsApp Formats...")
            pdf_path = pdf_generator.generate(newsletter_data)
            wa_path = whatsapp_formatter.generate(newsletter_data)
            
            st.success("✅ Generation Complete!")
            return pdf_path, wa_path
            
        except Exception as e:
            st.error(f"❌ Error during generation: {str(e)}")
            logger.exception("Streamlit generation error")
            return None, None

# === UI LAYOUT ===

st.title("🛡️ Cyber Intelligence Automation")
st.markdown("Generate business-class weekly cybersecurity briefings instantly.")

tab1, tab2, tab3 = st.tabs(["⚡ Dashboard", "⚙️ Configuration (.env)", "📂 Output Archives"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("### Control Center")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(
            "Pressing the button below will bypass the scheduler and manually trigger the intelligence gathering, "
            "AI synthesis, and report generation pipeline for the current week."
        )
        if st.button("🚀 Generate Newsletter Now", use_container_width=True):
            pdf_out, wa_out = generate_newsletter()
            
            if pdf_out and wa_out:
                st.balloons()
                st.markdown("### Downloads")
                with open(pdf_out, "rb") as f:
                    st.download_button("📥 Download PDF Report", f, file_name=os.path.basename(pdf_out), type="primary")
                with open(wa_out, "rb") as f:
                    st.download_button("📱 Download WhatsApp Text", f, file_name=os.path.basename(wa_out))
                    
    with col2:
        st.info(
            "**System Status**\n\n"
            "🟢 Engine: Ready\n\n"
            f"🕒 Timezone: `{TIMEZONE}`\n\n"
            f"📅 Current Week: `{get_week_label(TIMEZONE)}`\n\n"
            "🤖 AI Model: `gemini-1.5-flash`"
        )

# --- TAB 2: CONFIGURATION ---
with tab2:
    st.markdown("### Environment Configuration")
    st.markdown("Edit your API keys and recipient lists here. **Do not commit this file to public repositories.**")
    
    current_env = load_env_file()
    
    new_env = st.text_area(".env File Contents", value=current_env, height=300)
    
    if st.button("💾 Save Configuration"):
        save_env_file(new_env)
        st.success("Configuration saved! (Note: Restart may be required for some settings to take effect).")

# --- TAB 3: ARCHIVES ---
with tab3:
    st.markdown("### Generated Reports")
    output_dir = os.getenv("OUTPUT_DIR", "./output")
    
    if not os.path.exists(output_dir):
        st.info("No reports generated yet.")
    else:
        files = sorted(os.listdir(output_dir), reverse=True)
        if not files:
            st.info("No reports generated yet.")
        else:
            for file in files:
                filepath = os.path.join(output_dir, file)
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        btn = st.download_button(
                            label=f"Download {file}",
                            data=f,
                            file_name=file,
                            mime="application/pdf" if file.endswith(".pdf") else "text/plain"
                        )
