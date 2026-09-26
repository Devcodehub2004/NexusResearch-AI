"""
Streamlit UI for the multi-agent research pipeline.

Layout: a control panel on the left (topic input, run button, example
chips) and a live pipeline status board on the right — each agent's
card flips from WAITING -> RUNNING -> DONE as it actually executes.

Run with:
    streamlit run app.py
"""

import streamlit as st
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
from history import save_research, get_history, get_record, delete_record, clear_history


st.set_page_config(page_title="NexusResearch AI — Multi-Agent Deep Research", page_icon="🔬", layout="wide")

# ------------------------------------------------------------------
# Styling
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #0A0A0C;
        --card: #17171A;
        --card-border: #2A2A2E;
        --field: #1C1C1F;
        --field-border: #3A2A22;
        --accent-a: #FF5A1F;
        --accent-b: #FF8A3D;
        --text: #F2F2F3;
        --muted: #9CA3AF;
        --waiting: #6B7280;
        --running: #FF8A3D;
        --done: #4ADE80;
        --error: #F87171;
    }

    html, body, .stApp {
        background: radial-gradient(1100px 500px at 10% -5%, #2A1608 0%, var(--bg) 45%) !important;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2.4rem; max-width: 1180px; }
    * { font-family: 'Inter', -apple-system, sans-serif; }
    h1, h2, h3, p, span, div, label { color: var(--text); }

    .brand-title { font-size: 1.5rem; font-weight: 800; margin: 0; }
    .brand-sub { color: var(--muted); font-size: 0.88rem; margin-top: 0.3rem; }

    .field-label {
        font-size: 0.76rem; font-weight: 800; letter-spacing: 0.09em;
        color: var(--accent-b); text-transform: uppercase; margin: 1.8rem 0 0.6rem 0;
        display: flex; align-items: center; gap: 6px;
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #151519 !important;
        color: var(--text) !important;
        border: 1.5px solid rgba(255, 138, 61, 0.4) !important;
        border-radius: 12px !important;
        padding: 1rem 1.15rem !important;
        font-size: 1.02rem !important;
        line-height: 1.5 !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4), 0 0 14px rgba(255, 90, 31, 0.09) !important;
        transition: all 0.2s ease !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--accent-b) !important;
        box-shadow: 0 0 0 3.5px rgba(255, 138, 61, 0.22), 0 6px 24px rgba(255, 90, 31, 0.16) !important;
        background-color: #1A1A20 !important;
    }

    div[data-testid="stButton"] button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        border: none !important;
        transition: transform 0.12s ease, opacity 0.12s ease;
    }
    /* Primary run button */
    div[data-testid="stButton"]:has(button[kind="primary"]) button {
        background: linear-gradient(90deg, var(--accent-a), var(--accent-b)) !important;
        color: white !important;
        padding: 0.85rem 1rem !important;
        box-shadow: 0 8px 24px rgba(255, 90, 31, 0.25);
    }
    div[data-testid="stButton"]:has(button[kind="primary"]) button:hover { transform: translateY(-1px); }
    /* Chip buttons */
    div[data-testid="stButton"]:has(button[kind="secondary"]) button {
        background: var(--field) !important;
        color: var(--muted) !important;
        border: 1px solid var(--card-border) !important;
        padding: 0.5rem 0.9rem !important;
        font-size: 0.82rem !important;
    }
    div[data-testid="stButton"]:has(button[kind="secondary"]) button:hover {
        border-color: var(--accent-b) !important;
        color: var(--text) !important;
    }

    .try-label { color: var(--muted); font-size: 0.78rem; margin: 1.5rem 0 0.6rem 0; }

    .pipeline-title { font-size: 1.5rem; font-weight: 800; margin-bottom: 1.1rem; }

    .pcard {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1.15rem 1.3rem;
        margin-bottom: 0.9rem;
    }
    .pcard-top { display: flex; align-items: center; justify-content: space-between; }
    .pcard-left { display: flex; align-items: center; gap: 0.6rem; }
    .pnum { color: var(--accent-b); font-weight: 700; font-size: 0.85rem; }
    .ptitle { font-weight: 700; font-size: 1.02rem; }
    .pdesc { color: var(--muted); font-size: 0.86rem; margin-top: 0.4rem; }
    .pstatus {
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; padding: 0.25rem 0.65rem; border-radius: 20px;
        border: 1px solid currentColor;
    }

    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--card-border); gap: 1.2rem; }
    .stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 600; font-size: 0.88rem; }
    .stTabs [aria-selected="true"] { color: var(--accent-b) !important; }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--card); border: 1px solid var(--card-border); border-radius: 14px;
        padding: 1.6rem 1.8rem; margin-top: 0.8rem; color: var(--text); line-height: 1.65;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def stage_card_html(num: str, title: str, desc: str, status: str) -> str:
    color = {"WAITING": "var(--waiting)", "RUNNING": "var(--running)",
             "DONE": "var(--done)", "ERROR": "var(--error)"}[status]
    return f"""
    <div class="pcard">
        <div class="pcard-top">
            <div class="pcard-left">
                <span class="pnum">{num}</span>
                <span class="ptitle">{title}</span>
            </div>
            <span class="pstatus" style="color:{color};">{status}</span>
        </div>
        <div class="pdesc">{desc}</div>
    </div>
    """


STAGES = [
    ("01", "Search Agent", "Gathers recent web information"),
    ("02", "Reader Agent", "Scrapes & extracts deep content"),
    ("03", "Writer Chain", "Drafts the full research report"),
    ("04", "Critic Chain", "Reviews & scores the report"),
]

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "pending_topic" in st.session_state:
    st.session_state.topic_input = st.session_state.pop("pending_topic")
if "result_state" not in st.session_state:
    st.session_state.result_state = None
if "result_topic" not in st.session_state:
    st.session_state.result_topic = ""

# ------------------------------------------------------------------
# Sidebar - Search History
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📜 Research History")
    hist = get_history()
    if not hist:
        st.caption("No research history yet.")
    else:
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_history()
            st.session_state.result_state = None
            st.session_state.result_topic = ""
            st.rerun()

        for rec in hist:
            c1, c2 = st.columns([5, 1])
            with c1:
                topic_title = rec.get("topic", "Untitled")
                display_label = topic_title[:24] + ("..." if len(topic_title) > 24 else "")
                if st.button(
                    f"📄 {display_label}",
                    key=f"hist_{rec['id']}",
                    use_container_width=True,
                    help=f"{rec.get('timestamp', '')}: {topic_title}",
                ):
                    st.session_state.result_state = rec
                    st.session_state.result_topic = rec.get("topic", "")
                    st.rerun()
            with c2:
                if st.button("✕", key=f"del_{rec['id']}"):
                    delete_record(rec["id"])
                    st.rerun()

# ------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------
left_col, right_col = st.columns([1, 1.5], gap="large")

with left_col:
    st.markdown(
        """
        <div style="margin-bottom: 0.8rem;">
            <span style="font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; background: rgba(255, 90, 31, 0.15); color: #FF8A3D; padding: 4px 10px; border-radius: 999px; border: 1px solid rgba(255, 138, 61, 0.3);">
                Autonomous Intelligence
            </span>
            <h1 style="font-size: 2.1rem; font-weight: 800; margin: 0.6rem 0 0.2rem 0; letter-spacing: -0.02em; background: linear-gradient(135deg, #FFFFFF 30%, #FF8A3D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                NexusResearch AI
            </h1>
            <p style="color: var(--muted); font-size: 0.88rem; margin: 0; line-height: 1.4;">
                Autonomous 4-Agent Deep Research System • Search, Scrape, Synthesize & Critique
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="field-label"><span>🔍</span> <span>WHAT DO YOU WANT TO RESEARCH?</span></div>', unsafe_allow_html=True)
    topic = st.text_area(
        "Research topic",
        key="topic_input",
        height=105,
        label_visibility="collapsed",
        placeholder="Enter any research question, topic, or hypothesis in detail...\n\ne.g. What will be the impact of AI on the job market by 2030?",
    )

    run_clicked = st.button("⚡ Run Research Pipeline", type="primary", use_container_width=True)

    st.markdown('<div class="try-label">Try →</div>', unsafe_allow_html=True)
    for example in ["LLM agents 2025", "CRISPR gene editing", "Fusion energy progress"]:
        if st.button(example, key=f"chip_{example}", type="secondary", use_container_width=True):
            st.session_state.pending_topic = example
            st.rerun()

with right_col:
    st.markdown('<div class="pipeline-title">Pipeline</div>', unsafe_allow_html=True)
    placeholders = []
    for num, title, desc in STAGES:
        ph = st.empty()
        ph.markdown(stage_card_html(num, title, desc, "WAITING"), unsafe_allow_html=True)
        placeholders.append(ph)

# ------------------------------------------------------------------
# Run the pipeline, updating stage cards live as each agent finishes
# ------------------------------------------------------------------
if run_clicked:
    if not topic.strip():
        st.warning("Enter a research topic first.")
    else:
        state = {}
        try:
            # Stage 1 — Search
            placeholders[0].markdown(stage_card_html(*STAGES[0], "RUNNING"), unsafe_allow_html=True)
            search_agent = build_search_agent()
            search_result = search_agent.invoke({
                "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
            })
            state["search_results"] = search_result["messages"][-1].content
            placeholders[0].markdown(stage_card_html(*STAGES[0], "DONE"), unsafe_allow_html=True)

            # Stage 2 — Read
            placeholders[1].markdown(stage_card_html(*STAGES[1], "RUNNING"), unsafe_allow_html=True)
            reader_agent = build_reader_agent()
            reader_result = reader_agent.invoke({
                "messages": [(
                    "user",
                    f"""
Based on the following search results about '{topic}',
pick the single most relevant URL and scrape it for deeper content.

Search Results:
{state["search_results"][:3000]}
""",
                )]
            })
            state["scraped_content"] = reader_result["messages"][-1].content
            placeholders[1].markdown(stage_card_html(*STAGES[1], "DONE"), unsafe_allow_html=True)

            # Stage 3 — Write
            placeholders[2].markdown(stage_card_html(*STAGES[2], "RUNNING"), unsafe_allow_html=True)
            research_combined = (
                f"SEARCH RESULTS:\n{state['search_results']}\n\n"
                f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
            )
            state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
            placeholders[2].markdown(stage_card_html(*STAGES[2], "DONE"), unsafe_allow_html=True)

            # Stage 4 — Critique
            placeholders[3].markdown(stage_card_html(*STAGES[3], "RUNNING"), unsafe_allow_html=True)
            state["feedback"] = critic_chain.invoke({"report": state["report"]})
            placeholders[3].markdown(stage_card_html(*STAGES[3], "DONE"), unsafe_allow_html=True)
            st.session_state.result_state = state
            st.session_state.result_topic = topic
            save_research(topic, state)
        except Exception as e:
            st.error(f"Pipeline failed: {e}")

# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------
state = st.session_state.result_state
if state:
    st.markdown("---")
    st.markdown(f'<p class="pipeline-title">Results — {st.session_state.result_topic}</p>', unsafe_allow_html=True)

    tab_report, tab_critic, tab_search, tab_scraped = st.tabs(
        ["Report", "Critic Feedback", "Search Results", "Scraped Content"]
    )
    with tab_report:
        st.markdown(state.get("report", "No report generated."))
    with tab_critic:
        st.markdown(state.get("feedback", "No feedback generated."))
    with tab_search:
        st.markdown(state.get("search_results", "No search results."))
    with tab_scraped:
        st.markdown(state.get("scraped_content", "No scraped content."))

    st.download_button(
        "Download Report (Markdown)",
        data=state.get("report", ""),
        file_name=f"{st.session_state.result_topic.replace(' ', '_')}_report.md",
        mime="text/markdown",
    )