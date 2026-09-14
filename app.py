import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from agent.agent1.graph import run_agent_workflow as run_agent1_workflow
from agent.agent2.graph import run_agent_workflow as run_agent2_workflow
from evals.evaluator import evaluate_agent_execution
from agent.sql_tool import get_db_schema
from agent.registry import AGENT_REGISTRY, get_agent_config


def get_configured_api_key(key_name: str) -> str:
    """Read a provider key from Streamlit secrets first, then local environment.

    Secrets are available on Streamlit Community Cloud without ever exposing the
    key in the browser or committing it to source control.
    """
    try:
        secret_value = st.secrets.get(key_name, "")
    except (FileNotFoundError, AttributeError):
        secret_value = ""
    return str(secret_value or os.getenv(key_name, "")).strip()

# Streamlit Page Config
st.set_page_config(
    page_title="Eval-as-a-Service | Multi-Agent Evaluation Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0B0F17;
        color: #F1F5F9;
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
    }
    
    .hero-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.8) 50%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
    }
    .hero-title {
        background: linear-gradient(90deg, #F8FAFC 0%, #38BDF8 50%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .hero-sub {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    .glass-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        transition: all 0.25s ease;
    }
    .glass-card:hover {
        border-color: #38BDF8;
        transform: translateY(-3px);
    }
    .card-val {
        font-size: 1.9rem;
        font-weight: 800;
        margin: 4px 0;
    }
    .card-label {
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94A3B8;
        font-weight: 700;
    }
    
    .status-pill-green {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid #10B981;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.80rem;
        font-weight: 700;
    }
    .status-pill-blue {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid #38BDF8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.80rem;
        font-weight: 700;
    }
    .status-pill-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid #A855F7;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.80rem;
        font-weight: 700;
    }
    
    .node-timeline-box {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-left: 4px solid #38BDF8;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 14px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(15, 23, 42, 0.8);
        border: 1px solid #1E293B;
        border-radius: 10px 10px 0px 0px;
        padding: 0 24px;
        color: #94A3B8;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%) !important;
        color: #38BDF8 !important;
        border-bottom: 3px solid #38BDF8 !important;
    }

    /* Native Streamlit controls: give every interactive surface a distinct layer. */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111C2E 0%, #0B1220 100%);
        border-right: 1px solid rgba(56, 189, 248, 0.26);
        box-shadow: 14px 0 38px rgba(0, 0, 0, 0.20);
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding-top: 1.25rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        color: #F8FAFC;
    }
    .stApp p, .stApp label, .stApp .stCaption, .stApp [data-testid="stMarkdownContainer"] {
        color: #CBD5E1;
    }
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    [data-testid="stTextInput"] input {
        background: #172337 !important;
        border: 1px solid #36516F !important;
        color: #F8FAFC !important;
        border-radius: 10px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }
    [data-baseweb="select"] > div:hover,
    [data-baseweb="input"] > div:focus-within,
    [data-testid="stTextInput"] input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.16) !important;
    }
    [data-baseweb="select"] *, [data-testid="stTextInput"] input {
        color: #E2E8F0 !important;
    }
    [data-baseweb="popover"] [role="listbox"], [role="listbox"] {
        background: #172337 !important;
        border: 1px solid #36516F !important;
        color: #E2E8F0 !important;
    }
    [role="option"] { color: #E2E8F0 !important; }
    [role="option"]:hover, [role="option"][aria-selected="true"] {
        background: #243B57 !important;
    }
    .stButton > button {
        min-height: 2.7rem;
        background: linear-gradient(135deg, #1B3A57 0%, #243B63 100%);
        color: #EAF7FF !important;
        border: 1px solid #3A78A2;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.24);
        transition: all 0.18s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #075985 0%, #3730A3 100%);
        border-color: #7DD3FC;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(14, 165, 233, 0.20);
    }
    .stButton > button:focus-visible { outline: 3px solid #7DD3FC; outline-offset: 2px; }
    [data-testid="stChatInput"] {
        background: #121E31;
        border: 1px solid #36516F;
        border-radius: 14px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
    }
    [data-testid="stChatInput"] textarea {
        color: #F8FAFC !important;
        caret-color: #38BDF8;
    }
    [data-testid="stChatInput"] button {
        background: #0EA5E9 !important;
        color: #FFFFFF !important;
        border-radius: 9px;
    }
    [data-testid="stChatMessage"] {
        background: #111C2E;
        border: 1px solid #29445F;
        border-radius: 14px;
        padding: 0.3rem 0.6rem;
        margin-bottom: 0.85rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { color: #E2E8F0; }
    [data-testid="stExpander"] {
        background: #121E31;
        border: 1px solid #36516F !important;
        border-radius: 10px;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary { color: #BAE6FD !important; font-weight: 700; }
    [data-testid="stAlert"] {
        background: #102238 !important;
        color: #D7F1FF !important;
        border: 1px solid #2E81B5 !important;
        border-radius: 10px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #36516F;
        border-radius: 10px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] [role="grid"] { background: #121E31 !important; }
    [data-testid="stCodeBlock"] pre, .stCodeBlock pre {
        background: #07111F !important;
        border: 1px solid #28445F;
        color: #CFFAFE !important;
    }
    hr { border-color: #29445F !important; }
    ::selection { background: #0E7490; color: white; }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <h1 class="hero-title">⚡ Multi-Agent "Agent-as-a-Service" Platform</h1>
            <p class="hero-sub">Enterprise Multi-Agent Platform (E-Commerce Agent & Financial SaaS Agent) with Real-Time DeepEval Metrics</p>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <span class="status-pill-green">🟢 Groq Llama-3.3-70B API</span>
            <span class="status-pill-blue">⚡ ChromaDB Vector Stores</span>
            <span class="status-pill-purple">🛡️ Multi-Agent Benchmarks</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/circuit.png", width=55)
    st.title("🤖 Agent Selector & Config")
    
    # Global Sidebar Agent Selection Filter
    selected_agent_option = st.selectbox(
        "Active Agent Target",
        [
            "🛒 E-Commerce Operations Agent",
            "💳 Financial & SaaS Subscription Agent",
            "🌐 All Agents (Multi-Agent Comparative View)"
        ],
        index=0
    )
    
    # Resolve agent ID
    if "E-Commerce" in selected_agent_option:
        active_agent_id = "ecommerce"
    elif "Financial" in selected_agent_option:
        active_agent_id = "financial_saas"
    else:
        active_agent_id = "all"
        
    st.divider()
    st.subheader("⚙️ LLM Provider & Key")
    llm_provider = st.selectbox(
        "LLM Model Provider",
        ["Groq (llama-3.3-70b-versatile)", "OpenAI (gpt-4o-mini)", "Google Gemini (gemini-1.5-flash)"],
        index=0
    )

    provider_key_name = (
        "GROQ_API_KEY" if "Groq" in llm_provider
        else "OPENAI_API_KEY" if "OpenAI" in llm_provider
        else "GEMINI_API_KEY"
    )
    configured_api_key = get_configured_api_key(provider_key_name)
    api_key_override = st.text_input(
        "API Key for This Session (optional)",
        type="password",
        help="Used only for this browser session. Leave blank to use a server-side Streamlit secret or local .env value."
    )
    api_key_input = api_key_override.strip() or configured_api_key

    if configured_api_key and not api_key_override:
        st.success(f"🟢 {provider_key_name} loaded securely from server configuration.")
    elif api_key_override:
        st.info("🔐 Using the API key entered for this session only.")
    else:
        st.warning(f"Add {provider_key_name} in Streamlit secrets or enter it above to enable LLM responses.")

    st.divider()
    st.subheader("📊 Session Control")
    total_session_queries = len(st.session_state["query_history"])
    st.markdown(f"**Total Queries in Session**: `{total_session_queries}`")
    
    if st.button("🗑️ Reset Session History", use_container_width=True):
        st.session_state["query_history"] = []
        st.rerun()

    st.divider()
    st.subheader("🔍 Active Agent Schema")
    target_config = get_agent_config("ecommerce" if active_agent_id == "all" else active_agent_id)
    st.markdown(f"**Selected DB**: `{target_config['db_path'].name}`")
    st.markdown(f"**Chroma Collection**: `{target_config['chroma_collection']}`")
    with st.expander("Inspect SQLite Schema"):
        st.code(get_db_schema(target_config["db_path"]), language="sql")

# Tabs
tab1, tab2 = st.tabs(["💬 Multi-Agent Q&A Stream", "📈 Real-Time Visual Analytics & Comparative Benchmarks"])

# ==========================================
# TAB 1: MULTI-AGENT Q&A STREAM
# ==========================================
with tab1:
    st.markdown("### 💬 Interactive Q&A Agent Stream")
    
    current_agent_config = get_agent_config("ecommerce" if active_agent_id == "all" else active_agent_id)
    st.caption(f"Currently asking: **{current_agent_config['icon']} {current_agent_config['name']}**")
    
    # Dynamic Presets based on Active Agent
    st.markdown(f"**Presets for {current_agent_config['name']}:**")
    cp_cols = st.columns(len(current_agent_config["presets"]))
    preset_prompt = None
    
    for idx, preset in enumerate(current_agent_config["presets"]):
        if cp_cols[idx].button(preset["label"], use_container_width=True):
            preset_prompt = preset["query"]

    user_input = st.chat_input(f"Ask a question to {current_agent_config['name']}...")
    query_to_run = user_input or preset_prompt
    
    if query_to_run:
        target_id = "ecommerce" if active_agent_id == "all" else active_agent_id
        target_cfg = get_agent_config(target_id)
        
        with st.spinner(f"Executing {target_cfg['name']} Trajectory & DeepEval Metrics..."):
            if target_id == "financial_saas":
                agent_state = run_agent2_workflow(query_to_run, api_key=api_key_input, provider=llm_provider)
            else:
                agent_state = run_agent1_workflow(query_to_run, api_key=api_key_input, provider=llm_provider)
            agent_state["agent_id"] = target_id
            eval_results = evaluate_agent_execution(agent_state, api_key=api_key_input)
            
            query_num = len(st.session_state["query_history"]) + 1
            st.session_state["query_history"].append({
                "query_num": query_num,
                "agent_id": target_id,
                "agent_name": target_cfg["name"],
                "agent_icon": target_cfg["icon"],
                "question": query_to_run,
                "agent_state": agent_state,
                "eval_results": eval_results,
                "timestamp": time.strftime("%H:%M:%S")
            })

    # Render Chat Thread
    if not st.session_state["query_history"]:
        st.info(f"💡 No queries asked yet in this session. Select an agent in the sidebar, type a question, or click a preset chip!")
    else:
        for entry in st.session_state["query_history"]:
            q_num = entry["query_num"]
            q_text = entry["question"]
            ag_state = entry["agent_state"]
            ev_res = entry["eval_results"]
            a_icon = entry.get("agent_icon", "🤖")
            a_name = entry.get("agent_name", "AI Agent")
            
            # User Bubble
            with st.chat_message("user"):
                st.markdown(f"**Query #{q_num}** ({a_icon} {a_name}): {q_text}")
                
            # Assistant Bubble
            with st.chat_message("assistant"):
                intent_badge = "🟢 GROQ TEXT-TO-SQL" if ag_state["intent"] == "sql" else ("🔵 CHROMADB VECTOR RAG" if ag_state["intent"] == "rag" else "⚪ DIRECT")
                st.markdown(f"`{a_icon} {a_name.upper()}` | `{intent_badge}` | *Latency: {ag_state['latency_ms']} ms*")
                answer_source = ag_state.get("final_answer_source", "unknown")
                answer_model = ag_state.get("final_answer_model", "unknown")
                source_label = "✨ Final LLM response" if answer_source == "llm" else "⚠️ Fallback response (LLM unavailable)"
                st.caption(f"{source_label} · {answer_model}")
                st.markdown(ag_state["final_answer"])
                
                # DeepEval Score Pills
                ov_score = ev_res["overall_score"]
                t_score = ev_res["tool_correctness"]["score"]
                f_score = ev_res["faithfulness"]["score"]
                tox = ev_res["toxicity_safety"]
                tox_score = tox["score"]
                tox_label = tox["label"]
                p_tokens = ag_state["prompt_tokens"]
                c_tokens = ag_state["completion_tokens"]
                tot_tokens = p_tokens + c_tokens

                badge_style = "background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981;" if ov_score >= 80 else "background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B;"

                if tox_score >= 0.90:
                    tox_badge_style = "background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid #10B981;"
                elif tox_score >= 0.70:
                    tox_badge_style = "background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid #F59E0B;"
                else:
                    tox_badge_style = "background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid #EF4444;"

                st.markdown(f"""
                <div style="display: flex; gap: 10px; margin-top: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                    <span style="{badge_style} padding: 4px 12px; border-radius: 16px; font-weight: 700; font-size: 0.8rem;">
                        Overall Quality: {ov_score}%
                    </span>
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid #38BDF8; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">
                        Tool Selection: {t_score}
                    </span>
                    <span style="background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid #10B981; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">
                        Faithfulness: {f_score}
                    </span>
                    <span style="{tox_badge_style} padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; font-weight: 700;">
                        🛡️ Toxicity Safety: {tox_score} {tox_label}
                    </span>
                    <span style="background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid #A855F7; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">
                        🔢 Tokens: {tot_tokens} ({p_tokens} prompt / {c_tokens} comp)
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Collapsible Observability Trajectory & Payloads
                with st.expander(f"⛓️ View Query #{q_num} Execution Trajectory & Payloads"):
                    t_col1, t_col2 = st.columns([1.1, 1.0])
                    with t_col1:
                        st.markdown("**LangGraph State Trajectory:**")
                        for idx, step in enumerate(ag_state["execution_trace"]):
                            st.markdown(f"""
                            <div class="node-timeline-box">
                                <div style="display: flex; justify-content: space-between; font-weight: 700; color: #38BDF8;">
                                    <span>Node {idx+1}: {step['node']}</span>
                                    <span style="color: #94A3B8; font-size: 0.8rem;">{step['timestamp']} ({step['duration_ms']} ms)</span>
                                </div>
                                <div style="font-size: 0.9rem; margin-top: 4px; color: #E2E8F0;">{step['action']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    with t_col2:
                        if ag_state["intent"] == "sql":
                            st.markdown("**Generated Text-to-SQL:**")
                            st.code(ag_state.get("generated_sql", ""), language="sql")
                            if ag_state.get("sql_result"):
                                st.dataframe(pd.DataFrame(ag_state["sql_result"]), use_container_width=True)
                        elif ag_state["intent"] == "rag":
                            st.markdown("**Retrieved ChromaDB Vector Context:**")
                            for c in ag_state.get("retrieved_context", []):
                                st.caption(f"📌 **{c['doc_title']}** (Similarity Score: {c['score']})")
                                st.text(c['text'][:150] + "...")

# ==========================================
# TAB 2: MULTI-AGENT VISUAL ANALYTICS
# ==========================================
with tab2:
    st.markdown("### 📈 Real-Time Multi-Agent Visual Analytics & Benchmarks")
    st.caption("Filter real-time metric trends by Agent or view side-by-side comparative benchmarks across E-Commerce and Financial SaaS agents.")
    
    history = st.session_state["query_history"]
    
    if not history:
        st.info("💡 No metrics to display yet. Select an Agent and ask questions in Tab 1 to populate real-time analytics graphs!")
    else:
        records = []
        for h in history:
            q_num = h["query_num"]
            ev = h["eval_results"]
            ag = h["agent_state"]
            a_id = h.get("agent_id", "ecommerce")
            a_name = h.get("agent_name", "E-Commerce Agent")
            a_icon = h.get("agent_icon", "🛒")
            p_tok = ag.get("prompt_tokens", 140)
            c_tok = ag.get("completion_tokens", 90)
            tot_tok = p_tok + c_tok
            
            records.append({
                "Query": f"Q{q_num}",
                "Query_Index": q_num,
                "Agent_ID": a_id,
                "Agent": f"{a_icon} {a_name}",
                "Question": h["question"][:30] + "...",
                "Tool Selection": ev["tool_correctness"]["score"],
                "Reasoning Coherence": ev["reasoning_coherence"]["score"],
                "Step Efficiency": ev["trajectory_efficiency"]["score"],
                "Faithfulness": ev["faithfulness"]["score"],
                "Answer Relevancy": ev["answer_relevancy"]["score"],
                "Overall Quality (%)": ev["overall_score"],
                "Prompt Tokens": p_tok,
                "Completion Tokens": c_tok,
                "Total Tokens": tot_tok,
                "Latency (ms)": ag["latency_ms"]
            })
            
        df_history = pd.DataFrame(records)
        
        # Filter DataFrame by active_agent_id
        if active_agent_id != "all":
            df_filtered = df_history[df_history["Agent_ID"] == active_agent_id]
            if df_filtered.empty:
                st.warning(f"No queries recorded yet for active filter: {selected_agent_option}. Displaying overall session metrics.")
                df_filtered = df_history
        else:
            df_filtered = df_history

        # Section A: Production Hero Metric Banner Cards
        st.markdown(f"#### 🏆 Hero Performance Indicators ({'All Agents' if active_agent_id == 'all' else get_agent_config(active_agent_id)['name']})")
        hk1, hk2, hk3, hk4, hk5, hk6 = st.columns(6)
        
        avg_quality = df_filtered["Overall Quality (%)"].mean()
        avg_tool = df_filtered["Tool Selection"].mean()
        avg_faith = df_filtered["Faithfulness"].mean()
        avg_rel = df_filtered["Answer Relevancy"].mean()
        sum_tokens = df_filtered["Total Tokens"].sum()
        avg_lat = df_filtered["Latency (ms)"].mean()
        
        hk1.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #34D399;">
            <div class="card-label">Overall Quality</div>
            <div class="card-val" style="color: #34D399;">{avg_quality:.1f}%</div>
            <span class="status-pill-green">GRADE A</span>
        </div>
        """, unsafe_allow_html=True)

        hk2.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #38BDF8;">
            <div class="card-label">Tool Accuracy</div>
            <div class="card-val" style="color: #38BDF8;">{avg_tool:.2f}</div>
            <span class="status-pill-blue">OPTIMAL</span>
        </div>
        """, unsafe_allow_html=True)

        hk3.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #10B981;">
            <div class="card-label">Grounding Index</div>
            <div class="card-val" style="color: #10B981;">{avg_faith:.2f}</div>
            <span class="status-pill-green">VERIFIED</span>
        </div>
        """, unsafe_allow_html=True)

        hk4.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #FBBF24;">
            <div class="card-label">Answer Relevancy</div>
            <div class="card-val" style="color: #FBBF24;">{avg_rel:.2f}</div>
            <span class="status-pill-purple">ALIGNED</span>
        </div>
        """, unsafe_allow_html=True)

        hk5.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #C084FC;">
            <div class="card-label">Total Tokens</div>
            <div class="card-val" style="color: #C084FC;">{sum_tokens:,}</div>
            <span class="status-pill-purple">SESSION</span>
        </div>
        """, unsafe_allow_html=True)

        hk6.markdown(f"""
        <div class="glass-card" style="border-top: 4px solid #818CF8;">
            <div class="card-label">Avg Latency</div>
            <div class="card-val" style="color: #818CF8;">{avg_lat:.0f} ms</div>
            <span class="status-pill-blue">FAST</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Section B: Multi-Agent Comparative Benchmark View (if active_agent_id == 'all' or multiple agents present)
        if len(df_history["Agent_ID"].unique()) > 1:
            st.markdown("#### 🌐 Multi-Agent Comparative Benchmark View")
            st.caption("Side-by-side performance comparison across registered agents.")
            
            df_agent_comp = df_history.groupby("Agent")[["Tool Selection", "Reasoning Coherence", "Faithfulness", "Answer Relevancy", "Overall Quality (%)"]].mean().reset_index()
            
            fig_comp = px.bar(
                df_agent_comp,
                x="Agent",
                y=["Tool Selection", "Reasoning Coherence", "Faithfulness", "Answer Relevancy"],
                barmode="group",
                color_discrete_sequence=["#38BDF8", "#818CF8", "#10B981", "#FBBF24"],
                template="plotly_dark"
            )
            fig_comp.update_yaxes(range=[0, 1.15], gridcolor='#1E293B')
            fig_comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=30, b=30))
            st.plotly_chart(fig_comp, use_container_width=True)
            st.divider()

        # Section C: Real-Time Bar Charts with Padding
        st.markdown("#### 📈 Real-Time Metric & Token Bar Charts")
        
        def create_padded_bar_chart(df, y_col, title, color_hex, is_percent=False, is_token=False):
            fig = go.Figure()
            text_format = df[y_col].apply(lambda v: f"{v:.1f}%" if is_percent else (f"{v:,}" if is_token else f"{v:.2f}"))
            
            fig.add_trace(go.Bar(
                x=df["Query"],
                y=df[y_col],
                text=text_format,
                textposition="outside",
                cliponaxis=False,
                marker=dict(color=color_hex, opacity=0.85, line=dict(color=color_hex, width=1.5))
            ))
            
            max_y = df[y_col].max() if not df.empty else 1.0
            upper_limit = 115 if is_percent else (max_y * 1.25 if is_token else 1.20)
            
            fig.update_yaxes(range=[0, upper_limit], gridcolor='#1E293B', zeroline=False)
            fig.update_xaxes(type='category', gridcolor='#1E293B', tickfont=dict(size=12, color='#F1F5F9'))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=55, r=55, t=35, b=40),
                showlegend=False
            )
            return fig

        cg1, cg2, cg3 = st.columns(3)
        with cg1:
            st.markdown("##### 🛠️ Tool Selection & Schema Alignment")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Tool Selection", "Tool Selection", "#38BDF8"), use_container_width=True)

        with cg2:
            st.markdown("##### 🧠 Agent Reasoning Coherence (GEval)")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Reasoning Coherence", "Reasoning Coherence", "#818CF8"), use_container_width=True)

        with cg3:
            st.markdown("##### 📈 Step Trajectory Efficiency")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Step Efficiency", "Step Efficiency", "#F472B6"), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cg4, cg5, cg6 = st.columns(3)
        with cg4:
            st.markdown("##### 🛡️ Faithfulness (Grounding)")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Faithfulness", "Faithfulness", "#10B981"), use_container_width=True)

        with cg5:
            st.markdown("##### 🎯 Answer Relevancy")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Answer Relevancy", "Answer Relevancy", "#FBBF24"), use_container_width=True)

        with cg6:
            st.markdown("##### 🏆 Combined Overall Quality Index (%)")
            st.plotly_chart(create_padded_bar_chart(df_filtered, "Overall Quality (%)", "Overall Quality", "#34D399", is_percent=True), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Token Usage Chart
        st.markdown("##### 🔢 Session Token Usage (Prompt vs Completion Tokens per Query)")
        fig_tok = go.Figure()
        fig_tok.add_trace(go.Bar(
            x=df_filtered["Query"], y=df_filtered["Prompt Tokens"], name="Prompt Tokens",
            marker_color="#818CF8", text=df_filtered["Prompt Tokens"], textposition="inside"
        ))
        fig_tok.add_trace(go.Bar(
            x=df_filtered["Query"], y=df_filtered["Completion Tokens"], name="Completion Tokens",
            marker_color="#C084FC", text=df_filtered["Completion Tokens"], textposition="inside"
        ))
        fig_tok.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=55, r=55, t=35, b=40),
            legend_title_text="Token Type",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_tok.update_xaxes(type='category', gridcolor='#1E293B')
        fig_tok.update_yaxes(gridcolor='#1E293B')
        st.plotly_chart(fig_tok, use_container_width=True)

        st.divider()

        # Section D: Cumulative Session Details Table
        st.markdown("#### 📑 Cumulative Session Query Details Table")
        st.dataframe(
            df_history,
            column_config={
                "Overall Quality (%)": st.column_config.ProgressColumn(
                    "Overall Quality (%)",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            },
            use_container_width=True,
            hide_index=True
        )
