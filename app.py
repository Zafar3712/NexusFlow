import streamlit as st
import pandas as pd
import requests
import time
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie
from database import setup_database, load_uploaded_file, get_schema, get_ui_schema
from agent import generate_and_execute_sql, model

# --- Helper Functions ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# --- INNOVATION 1: THE CHATGPT EFFECT (STREAMING) ---
def stream_text(text, speed=0.02):
    """Creates a typewriter effect for AI text responses."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(speed)

# --- INNOVATION 2: ZERO-SHOT CACHING ---
@st.cache_data(show_spinner=False, hash_funcs={"duckdb.DuckDBPyConnection": lambda _: None})
def fetch_insight_cached(user_query, current_schema, _db_connection):
    """Caches the exact SQL and Dataframe if the same question is asked twice."""
    return generate_and_execute_sql(user_query, current_schema, _db_connection)

# --- 1. PAGE CONFIGURATION & CSS INJECTION ---
st.set_page_config(page_title="NexusFlow", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700;800&display=swap');
    
    html, body, [class*="css"], p, div, button, input {
        font-family: 'Inter', sans-serif !important;
    }
    
    span[class*="material"], .stIcon, .st-emotion-cache-1vt4ygl, span.material-symbols-rounded {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: -0.5px;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main .block-container {
        animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    [data-testid="stSidebar"] > div:first-child {
        animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    [data-testid="stSidebar"] {
        min-width: 280px !important;
        max-width: 300px !important;
        background-color: rgba(248, 250, 252, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
    }

    [data-testid="stChatInput"] {
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.15), 0 8px 10px -6px rgba(79, 70, 229, 0.1);
        border-radius: 16px !important;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    [data-testid="stChatInput"]:focus-within {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(79, 70, 229, 0.2), 0 8px 10px -6px rgba(79, 70, 229, 0.1);
        border-color: #4F46E5;
    }

    [data-testid="stAudioInput"] {
        border-radius: 16px !important;
        border: 1px solid #E2E8F0;
        background-color: #F8FAFC;
        padding: 5px;
    }

    /* --- VISUAL POLISH: Sleek Tabs --- */
    [data-testid="stTabs"] button {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: background-color 0.2s ease;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #F8FAFC;
        border-bottom-color: #4F46E5 !important;
    }
    [data-testid="stTabs"] button:hover {
        background-color: #F1F5F9;
    }

    .animated-title {
        background: linear-gradient(-45deg, #4F46E5, #EC4899, #3B82F6, #4F46E5);
        background-size: 300%;
        font-weight: 800;
        font-size: 4rem;
        letter-spacing: -2px;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-shift 6s ease infinite;
        margin-bottom: -10px;
        padding-bottom: 0px;
        font-family: 'Poppins', sans-serif !important;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    [data-testid="stSidebar"] h3 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1E293B;
        margin-bottom: 5px !important;
        padding-top: 0px !important;
    }
    
    [data-testid="stFileUploadDropzone"] {
        padding: 5px !important;
        min-height: 50px !important;
        border-radius: 8px !important;
        border: 1.5px dashed #CBD5E1 !important;
        background-color: rgba(255, 255, 255, 0.5) !important;
    }
    
    [data-testid="stFileUploadDropzone"] svg { display: none !important; }
    [data-testid="stFileUploadDropzone"] small { display: none !important; }
    
    [data-testid="stFileUploadDropzone"] div {
        font-size: 0.85rem !important;
        color: #64748B !important;
        font-weight: 500;
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 2.2rem !important;
        height: 2.2rem !important;
        font-size: 0.9rem !important;
        font-weight: 500;
        border-radius: 6px !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
    }
    
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.7);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.08);
        border-color: #4F46E5;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #64748B !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: #4F46E5 !important;
    }
    
    .pulsing-text {
        animation: pulse 1.5s infinite;
        color: #4F46E5;
        font-weight: 600;
    }
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    </style>
""", unsafe_allow_html=True)

# Global Keyboard Shortcut
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === '/' && doc.activeElement.tagName !== 'TEXTAREA' && doc.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            const chatInput = doc.querySelector('[data-testid="stChatInput"] textarea');
            if (chatInput) {
                chatInput.focus();
            }
        }
    });
    </script>
    """,
    height=0,
    width=0,
)

# Initialize Session State
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = setup_database()
if 'schema' not in st.session_state:
    st.session_state.schema = "No data uploaded yet."
if 'ui_schema' not in st.session_state:
    st.session_state.ui_schema = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'quick_prompt' not in st.session_state:
    st.session_state.quick_prompt = None
if 'dataset_stats' not in st.session_state:
    st.session_state.dataset_stats = None

lottie_url = "https://assets5.lottiefiles.com/packages/lf20_qp1q7mct.json"
lottie_json = load_lottieurl(lottie_url)

# --- 2. SIDEBAR: UPLOAD, METADATA & CONTROL ---
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
            </svg>
            <h3 style="margin: 0; padding: 0;">Data Config</h3>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("upload_hidden", type=["csv", "parquet"], label_visibility="collapsed")
    
    if uploaded_file:
        if st.button("Load Dataset", type="primary", use_container_width=True):
            with st.spinner("Ingesting data..."):
                st.session_state.dataset_stats = load_uploaded_file(st.session_state.db_conn, uploaded_file)
                st.session_state.schema = get_schema(st.session_state.db_conn)
                st.session_state.ui_schema = get_ui_schema(st.session_state.db_conn)
                fetch_insight_cached.clear()
                st.toast('Dataset loaded successfully!') 
    
    st.divider()
    
    if st.session_state.dataset_stats:
        st.markdown("### Dataset Health")
        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Total Rows", st.session_state.dataset_stats["rows"])
        with metric_col2:
            st.metric("Columns", st.session_state.dataset_stats["cols"])
        st.divider()

    st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"></line>
                <line x1="8" y1="12" x2="21" y2="12"></line>
                <line x1="8" y1="18" x2="21" y2="18"></line>
                <line x1="3" y1="6" x2="3.01" y2="6"></line>
                <line x1="3" y1="12" x2="3.01" y2="12"></line>
                <line x1="3" y1="18" x2="3.01" y2="18"></line>
            </svg>
            <h3 style="margin: 0; padding: 0;">Available Fields</h3>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.ui_schema:
        st.markdown(st.session_state.ui_schema)
    else:
        st.caption("Waiting for data upload...")
        
    st.divider()
    
    if st.session_state.messages:
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# --- 3. MAIN INTERFACE ---
st.markdown('<h1 class="animated-title">NexusFlow</h1>', unsafe_allow_html=True)
st.markdown("<h4 style='color: #475569; margin-top: 5px; margin-bottom: 25px;'>Autonomous Text-to-Dashboard Orchestration</h4>", unsafe_allow_html=True)
st.divider()

if not st.session_state.messages:
    if st.session_state.schema == "No data uploaded yet.":
        col1, col2 = st.columns([1, 2])
        with col1:
            if lottie_json:
                st_lottie(lottie_json, height=250, key="welcome_animation")
        with col2:
            st.write("") 
            st.write("")
            st.markdown("<h2>Welcome to the future of Data Analytics.</h2>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 1.1rem; color: #475569;'>NexusFlow eliminates the need for SQL or Python. Simply drop your <code>.csv</code> or <code>.parquet</code> file into the sidebar, and start asking questions in plain English.</p>", unsafe_allow_html=True)
            st.info("**Upload a dataset in the sidebar to begin.**")
            st.caption("Pro Tip: Press **`/`** anywhere on your keyboard to instantly focus the chat input.")
    else:
        st.success("**Dataset Active.** Ask a question below, or try one of these suggestions:")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Show me a summary of the data", use_container_width=True):
                st.session_state.quick_prompt = "Give me a summary of the dataset with counts or totals."
                st.rerun()
        with col2:
            if st.button("Find the top categories", use_container_width=True):
                st.session_state.quick_prompt = "What are the top categories by count or value? Show as a bar chart."
                st.rerun()
        with col3:
            if st.button("Show trend over time", use_container_width=True):
                st.session_state.quick_prompt = "Show me the trend of the data over time as a line chart."
                st.rerun()

# Render Chat History
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant" and "data" in msg and msg["data"] is not None:
            df_hist = msg["data"]
            
            if df_hist.shape == (1, 1):
                col_name = df_hist.columns[0]
                val = df_hist.iloc[0, 0]
                st.metric(label=str(col_name).upper(), value=str(val))
                with st.expander("View SQL Engine"):
                    st.code(msg["sql"], language='sql')
            else:
                tab_viz, tab_data, tab_sql = st.tabs(["Visualization", "Editable Raw Data", "SQL Engine"])
                
                with tab_viz:
                    if "fig" in msg and msg["fig"] is not None:
                        st.plotly_chart(msg["fig"], use_container_width=True, key=f"history_chart_{i}")
                    else:
                        st.caption("No visualization required for this data shape.")
                
                with tab_data:
                    # --- INNOVATION: Editable Data Sandbox in Vertical View ---
                    st.caption("✏️ *Double-click any cell to edit. Your edits will export if you download the CSV.*")
                    edited_df = st.data_editor(df_hist, use_container_width=True, key=f"editor_{i}")
                
                with tab_sql:
                    if "sql" in msg:
                        st.code(msg["sql"], language='sql')
            
            st.feedback("thumbs", key=f"feedback_{i}")
            
            if i == len(st.session_state.messages) - 1 and df_hist.shape != (1, 1):
                st.divider()
                st.caption("**Explore Further:**")
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                with f_col1:
                    if st.button("Show as Percentages", key=f"f1_{i}", use_container_width=True):
                        st.session_state.quick_prompt = "Convert the previous result into percentages."
                        st.rerun()
                with f_col2:
                    if st.button("Sort Highest to Lowest", key=f"f2_{i}", use_container_width=True):
                        st.session_state.quick_prompt = "Sort the previous data from highest to lowest."
                        st.rerun()
                with f_col3:
                    if st.button("Show Trend Over Time", key=f"f3_{i}", use_container_width=True):
                        st.session_state.quick_prompt = "Extract the date/time and show the trend over time."
                        st.rerun()
                with f_col4:
                    # Point the export feature to the new edited_df
                    csv_data = edited_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Export CSV",
                        data=csv_data,
                        file_name=f"nexusflow_extract_{i}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"dl_{i}"
                    )

# --- 4. INPUT HANDLING (Multimodal Voice + Text) ---
user_input = None

if hasattr(st, "audio_input"):
    audio_value = st.audio_input("Speak your query (Auto-submits when you stop recording):")
    if audio_value:
        with st.spinner("Listening and Transcribing..."):
            try:
                transcription_prompt = "Transcribe the following audio accurately. Return ONLY the exact text transcript, no markdown, no conversational filler."
                response = model.generate_content([
                    transcription_prompt,
                    {
                        "mime_type": "audio/wav",
                        "data": audio_value.getvalue()
                    }
                ])
                user_input = response.text.strip()
                st.toast(f"Recognized: '{user_input}'")
            except Exception as e:
                st.error(f"Voice transcription failed. Error: {e}")

text_input = st.chat_input("Press '/' to search, or type here...")
if text_input:
    user_input = text_input

if st.session_state.quick_prompt:
    user_input = st.session_state.quick_prompt
    st.session_state.quick_prompt = None

if user_input:
    if st.session_state.schema == "No data uploaded yet.":
        st.toast("Please upload a dataset in the sidebar first!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.status("Orchestrating Insight...", expanded=True) as status:
                st.markdown('<p class="pulsing-text">Translating intent to Agentic SQL...</p>', unsafe_allow_html=True)
                
                df, sql = fetch_insight_cached(user_input, st.session_state.schema, st.session_state.db_conn)
                
                # --- INNOVATION: Auto-Healing SQL Loop ---
                if df is None:
                    st.warning("DuckDB syntax warning. Initiating Agentic Auto-Healing...")
                    time.sleep(1.5) # Simulate LLM thinking pacing
                    st.markdown('<p class="pulsing-text">Agent analyzing syntax error and rewriting SQL (Attempt 2)...</p>', unsafe_allow_html=True)
                    healing_prompt = f"Previous query failed. Fix the SQL for: {user_input}"
                    df, sql = fetch_insight_cached(healing_prompt, st.session_state.schema, st.session_state.db_conn)

                if df is not None:
                    if df.empty:
                        status.update(label="Query Successful, but No Data Found", state="complete", expanded=False)
                        response_text = "I successfully filtered the data, but no records matched your request."
                        st.warning(response_text)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text,
                            "data": None,
                            "sql": sql
                        })
                        st.rerun() 
                    else:
                        st.markdown('<p class="pulsing-text">SQL executed successfully. Synthesizing Interface...</p>', unsafe_allow_html=True)
                        
                        fig_to_store = None
                        if df.shape != (1, 1):
                            ui_prompt = f"""
                            You are an expert Data Visualization Agent in an HCI framework.
                            The user's original goal was: "{user_input}"
                            
                            Here is a sample of the resulting pandas dataframe named 'df':
                            {df.head(3).to_string()}
                            
                            Your task is to CHOOSE THE MOST APPROPRIATE Plotly chart type based on the user's intent and data shape.
                            Write Python code using Plotly Express (px) to create this visualization. 
                            Assign the plotly figure to a variable named 'fig'.
                            Return ONLY raw Python code. No markdown formatting, no explanations.
                            """
                            
                            ui_response = model.generate_content(ui_prompt)
                            code_to_exec = ui_response.text.strip().replace('```python', '').replace('```', '')
                            
                            try:
                                local_vars = {'df': df, 'px': __import__('plotly.express').express}
                                exec(code_to_exec, globals(), local_vars)
                                if 'fig' in local_vars:
                                    fig_to_store = local_vars['fig']
                            except Exception:
                                pass 
                        
                        status.update(label="Analysis Complete!", state="complete", expanded=False)
                        
                        response_text = "Here is your orchestrated dashboard:"
                        st.write_stream(stream_text(response_text))
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_text,
                            "data": df,
                            "fig": fig_to_store,
                            "sql": sql
                        })
                        st.rerun() 
                    
                else:
                    status.update(label="Execution Failed", state="error", expanded=True)
                    error_message = f"Failed to retrieve data after auto-healing attempts. Here is the internal error:\n\n```text\n{sql}\n```"
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_message
                    })
                    st.rerun()