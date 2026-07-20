import time
import html
from datetime import datetime, date, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from services.db_services import (
    init_db,
    reset_demo_database,
    save_analysis_and_actions,
    get_actions,
    update_action_status,
    update_action_due_date,
    get_pending_actions_for_regulation,
    get_carryover_actions,
    get_versions_for_regulation,
)

from services.version_service import process_pdf_versions
from services.openai_service import analyze_regulatory_change
from services.source_service import fetch_regulatory_sources


st.set_page_config(
    page_title="LexaFlow AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()


# ---------------- CSS ----------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(8,17,34,0.98));
    border: 1px solid rgba(59,130,246,0.45);
    border-radius: 18px;
    padding: 22px 24px;
    min-height: 140px;
    box-shadow: 0 0 24px rgba(37,99,235,0.16);
}

div[data-testid="stMetricLabel"] {
    color: #dbeafe !important;
    font-size: 15px !important;
    font-weight: 900 !important;
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 38px !important;
    font-weight: 900 !important;
}
.block-container {
    padding-top: 0.8rem;
    padding-left: 1.6rem;
    padding-right: 1.6rem;
    max-width: 100% !important;
}

[data-testid="stSidebar"] {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

:root {
    --bg-main: #050b16;
    --card-bg: rgba(15,23,42,0.92);
    --card-bg-soft: rgba(15,23,42,0.65);
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --border-soft: rgba(148,163,184,0.22);
    --blue: #2563eb;
    --cyan: #38bdf8;
    --green: #22c55e;
    --red: #ef4444;
    --orange: #f59e0b;
    --purple: #a78bfa;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(14,165,233,0.12), transparent 28%),
        #050b16;
    color: var(--text-main);
}

h1, h2, h3, h4 {
    letter-spacing: -0.03em;
}

/* TOP HEADER */
.neo-header {
    width: 100%;
    height: 140px;
    padding: 26px 34px;
    border-radius: 22px;
    display: flex;
    align-items: center;
    overflow: hidden;
}

.neo-title {
    font-size: 44px;
    line-height: 1.15;
    font-weight: 900;
    white-space: nowrap;
}
.neo-section {
    font-size: 18px;
    margin-top: 6px;
    font-weight: 700;
    color: #dbeafe;
}

.profile-card {
    min-height: 96px;
    border-radius: 18px;
    padding: 14px 18px;
    background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(30,41,59,0.82));
    border: 1px solid rgba(96,165,250,0.35);
    color: white;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 0 22px rgba(37,99,235,0.14);
}

.profile-avatar {
    width: 46px;
    height: 46px;
    border-radius: 999px;
    background: linear-gradient(135deg, #2563eb, #38bdf8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

.profile-name {
    font-weight: 900;
    font-size: 15px;
}

.profile-role {
    color: #cbd5e1;
    font-size: 12px;
    margin-top: 2px;
}

.profile-access {
    color: #93c5fd;
    font-size: 11px;
    margin-top: 4px;
}

/* BUTTONS */
.stButton > button {
    min-height: 52px !important;
    border-radius: 14px !important;
    font-weight: 800 !important;
    transition: all 0.2s ease-in-out !important;
    border: 1px solid rgba(148,163,184,0.25) !important;
    background: rgba(15,23,42,0.72) !important;
    color: #e5e7eb !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    border-color: #3b82f6 !important;
    box-shadow: 0 0 22px rgba(59,130,246,0.35);
}

.stButton > button[kind="primary"] {
    min-height: 58px !important;
    background: linear-gradient(90deg, #ef4444, #f97316) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 0 24px rgba(249,115,22,0.35);
}

/* SECTIONS */
.section-heading {
    font-size: 26px;
    font-weight: 900;
    margin: 24px 0 14px 0;
    color: #f8fafc;
}

/* AGENT FLOW */
.agent-card {
    background: linear-gradient(180deg, rgba(12,24,48,0.98), rgba(3,10,24,0.98));
    border: 1px solid rgba(96,165,250,0.30);
    border-radius: 18px;
    min-height: 178px;
    padding: 18px 12px;
    text-align: center;
    box-shadow: 0 0 20px rgba(37,99,235,0.10);
}

.agent-running {
    border: 2px solid #38bdf8;
    box-shadow: 0 0 26px rgba(56,189,248,0.45);
    animation: pulseGlow 1.2s infinite;
}

.agent-done {
    border-color: #22c55e;
    background: linear-gradient(180deg, rgba(6,78,59,0.45), rgba(2,6,23,0.94));
}

.agent-skipped {
    border-color: #f59e0b;
    background: linear-gradient(180deg, rgba(120,53,15,0.35), rgba(2,6,23,0.94));
}

@keyframes pulseGlow {
    0% { transform: scale(1); box-shadow: 0 0 0 rgba(56,189,248,0); }
    50% { transform: scale(1.025); box-shadow: 0 0 28px rgba(56,189,248,0.45); }
    100% { transform: scale(1); box-shadow: 0 0 0 rgba(56,189,248,0); }
}

.agent-num {
    float: left;
    width: 30px;
    height: 30px;
    border-radius: 999px;
    background: rgba(30,41,59,0.95);
    color: #dbeafe;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
}

.agent-icon {
    font-size: 40px;
    margin-top: 18px;
}

.agent-title {
    font-size: 16px;
    font-weight: 900;
    margin-top: 10px;
}

.agent-status {
    display: inline-block;
    margin-top: 8px;
    padding: 5px 14px;
    border-radius: 999px;
    background: rgba(51,65,85,0.8);
    font-size: 13px;
}

.agent-desc {
    color: #cbd5e1;
    font-size: 13px;
    margin-top: 10px;
}

/* SUMMARY */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(2,6,23,0.96));
    border: 1px solid rgba(59,130,246,0.32);
    border-radius: 18px;
    padding: 18px 20px;
    min-height: 128px;
    box-shadow: 0 0 28px rgba(30,64,175,0.12);
}

div[data-testid="stMetricLabel"] {
    color: #cbd5e1 !important;
    font-size: 15px !important;
    font-weight: 800 !important;
}

div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 34px !important;
    font-weight: 900 !important;
}

/* CONTENT CARDS */
.clean-card {
    background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(2,6,23,0.95));
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 18px;
    padding: 22px;
    min-height: 245px;
    box-shadow: 0 0 30px rgba(15,23,42,0.35);
}

.readable-box {
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
    background: rgba(15,23,42,0.60);
}

.badge-green {
    background:#dcfce7;
    color:#16a34a;
    padding:7px 12px;
    border-radius:999px;
    font-weight:800;
    display:inline-block;
    margin:4px;
}

.badge-blue {
    background: rgba(30,64,175,0.55);
    color: #bfdbfe;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 700;
    display: inline-block;
    margin: 4px;
}

.badge-red {
    background: rgba(127,29,29,0.60);
    color: #fecaca;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 800;
    display: inline-block;
}

.badge-orange {
    background: rgba(120,53,15,0.60);
    color: #fbbf24;
    padding: 6px 12px;
    border-radius: 999px;
    font-weight: 800;
    display: inline-block;
}

.small-muted {
    color: #94a3b8;
    font-size: 13px;
}

.scroll-box {
    max-height: 390px;
    overflow-y: auto;
    padding-right: 8px;
}

.role-card {
    border-radius: 18px;
    padding: 18px;
    border: 1px solid rgba(148,163,184,0.22);
    background: rgba(37,99,235,0.10);
}

.footer-center {
    text-align: center;
    color: #94a3b8;
    margin-top: 22px;
    margin-bottom: 10px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------- STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "Command Center"

if "agent_status" not in st.session_state:
    st.session_state.agent_status = {}

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "latest_ai" not in st.session_state:
    st.session_state.latest_ai = None


# ---------------- HELPERS ----------------
def set_agent(key, status):
    st.session_state.agent_status[key] = status


def get_progress_percent():
    total = 7
    completed = sum(
        1 for value in st.session_state.agent_status.values()
        if value in ["done", "skipped"]
    )
    return int((completed / total) * 100)


def render_agent_flow(active=None):
    agents = [
        ("monitor", "📡", "Monitor", "Checks input"),
        ("extract", "📄", "Extraction", "Extracts text"),
        ("version", "🔄", "Version", "Compares version"),
        ("analyze", "🧠", "Change Analyst", "Runs if changed"),
        ("impact", "⚠️", "Impact", "Assesses impact"),
        ("action", "✅", "Action Planner", "Creates tasks"),
        ("notify", "🔔", "Notification", "Alerts if needed"),
    ]

    progress = get_progress_percent()

    p1, p2, p3 = st.columns([1, 2, 1])
    with p2:
        st.markdown(
            f"<div style='text-align:center;font-weight:800;color:#cbd5e1;'>Pipeline Progress: {progress}%</div>",
            unsafe_allow_html=True,
        )
        st.progress(progress)

    cols = st.columns(len(agents))

    for idx, (col, (key, icon, title, desc)) in enumerate(zip(cols, agents), start=1):
        status = st.session_state.agent_status.get(key, "pending")

        css = "agent-card"
        label = "Pending"

        if active == key:
            css += " agent-running"
            label = "Running"
        elif status == "done":
            css += " agent-done"
            label = "Completed"
        elif status == "skipped":
            css += " agent-skipped"
            label = "Skipped"

        with col:
            st.markdown(
                f"""
                <div class="{css}">
                    <div class="agent-num">{idx}</div>
                    <div class="agent-icon">{icon}</div>
                    <div class="agent-title">{title}</div>
                    <div class="agent-status">{label}</div>
                    <div class="agent-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def parse_due_date(due_date_value):
    try:
        if not due_date_value:
            return date.today() + timedelta(days=7)

        if "days" in str(due_date_value):
            days = int(str(due_date_value).split()[0])
            return date.today() + timedelta(days=days)

        return datetime.strptime(str(due_date_value), "%Y-%m-%d").date()

    except Exception:
        return date.today() + timedelta(days=7)


def render_due_date_status(due_date_value, status):
    due = parse_due_date(due_date_value)

    if status != "Completed" and due < date.today():
        st.error(f"⚠️ Overdue: {due}")
    elif status != "Completed" and due == date.today():
        st.warning(f"⏰ Due today: {due}")
    else:
        st.caption(f"Due: {due}")

    return due


def render_executive_summary(ai_result, result=None):
    if not ai_result:
        st.markdown("## 📌 Executive Summary")

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric("🔎 Changes", 0)
        c2.metric("👥 Teams", 0)
        c3.metric("✅ Actions", 0)
        c4.metric("🚨 Risk", "None")
        c5.metric("🤖 AI Confidence", "0%")
        c6.metric("🚩 Status", "Ready")
        return

    changes = len(ai_result.get("what_changed", []))
    teams = len(ai_result.get("affected_teams", []))
    actions = len(ai_result.get("recommended_actions", []))
    risk = str(ai_result.get("risk_level", "Unknown")).title()
    confidence = int(float(ai_result.get("confidence_score", 0.85)) * 100)

    status = "Needs Action"
    if result and not result.get("change_detected"):
        status = "No New Change"

    st.markdown("## 📌 Executive Summary")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("🔎 Changes", changes)
    c2.metric("👥 Teams", teams)
    c3.metric("✅ Actions", actions)
    c4.metric("🚨 Risk", risk)
    c5.metric("🤖 AI Confidence", f"{confidence}%")
    c6.metric("🚩 Status", status)

def get_change_items(ai_result):
    what_changed = ai_result.get("what_changed", [])

    if isinstance(what_changed, dict):
        return [str(k).replace("_", " ").title() for k in list(what_changed.keys())[:5]]

    if isinstance(what_changed, list):
        return [str(x).replace("_", " ").title() for x in what_changed[:5]]

    return [str(what_changed)]


def render_dashboard_insights(ai_result):
    if not ai_result:
        return

    business_impact = ai_result.get("business_impact", {})
    teams = ai_result.get("affected_teams", [])
    change_items = get_change_items(ai_result)

    st.markdown("## 📊 Regulatory Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("### 🔄 Change Overview")
            st.markdown(" ")
            for item in change_items:
                st.markdown(f"🔹 **{item}** &nbsp; <span class='badge-blue'>Updated</span>", unsafe_allow_html=True)
            st.markdown(" ")
            st.caption("View full details in Change Analysis")

    with col2:
        with st.container(border=True):
            st.markdown("### ⚠️ Impact Summary")
            st.markdown(" ")
            if isinstance(business_impact, dict):
                for idx, (key, value) in enumerate(list(business_impact.items())[:4]):
                    severity = "High" if idx < 2 else "Medium"
                    badge = "badge-red" if severity == "High" else "badge-orange"
                    st.markdown(
                        f"• **{str(key).replace('_', ' ').title()}** "
                        f"<span class='{badge}'>{severity}</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.warning(str(business_impact))
            st.markdown(" ")
            st.caption("View full impact in Change Analysis")

    with col3:
        with st.container(border=True):
            st.markdown("### 👥 Teams Affected")
            st.markdown(" ")
            if teams:
                for team in teams[:8]:
                    st.markdown(f"<span class='badge-green'>{html.escape(str(team))}</span>", unsafe_allow_html=True)
            else:
                st.info("No teams identified yet.")
            st.markdown(" ")
            st.caption("Ownership can be reviewed in Action Tracker")


def render_readable_ai_output(ai_result):

    if not ai_result:
        st.warning("AI analysis was skipped because no new document change was detected.")
        return

    what_changed = ai_result.get("what_changed", {})
    business_impact = ai_result.get("business_impact", {})

    st.markdown("## 🔄 What Changed")

    if isinstance(what_changed, dict):

        for key, value in what_changed.items():

            with st.container(border=True):

                st.markdown(f"### {str(key).replace('_', ' ').title()}")

                if isinstance(value, dict):

                    old_value = value.get("old", "N/A")
                    new_value = value.get("new", "N/A")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Previous")
                        st.info(old_value)

                    with col2:
                        st.markdown("#### Updated")
                        st.success(new_value)

                else:
                    st.success(str(value))

    elif isinstance(what_changed, list):

        cols = st.columns(2)

        for idx, item in enumerate(what_changed):

            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(f"### {str(item).replace('_', ' ').title()}")
                    st.success("Updated")

    st.markdown("## ⚠️ Why It Matters")

    if isinstance(business_impact, dict):

        cols = st.columns(2)

        items = list(business_impact.items())

        for idx, (key, value) in enumerate(items):

            with cols[idx % 2]:

                with st.container(border=True):

                    st.markdown(
                        f"### {str(key).replace('_', ' ').title()}"
                    )

                    st.write(value)

    else:

        st.warning(str(business_impact))


# ---------------- TOP BAR ----------------
page = st.session_state.page

top_l, top_run, top_reset, top_profile = st.columns([5.0, 1.4, 1.4, 2.0])

with top_l:
    st.markdown(
        f"""
        <div class="neo-header">
            <div>
                <div class="neo-title">⚖️ LexaFlow AI</div>
                <div class="neo-section">Autonomous Regulatory Intelligence Command Center</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_run:
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    run_clicked = st.button("▶ Run Monitor", type="primary", use_container_width=True)

with top_reset:
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    reset_clicked_global = st.button("🔄 Reset Demo", type="primary", use_container_width=True)

with top_profile:
    st.markdown(
        """
        <div class="profile-card">
            <div class="profile-avatar">👤</div>
            <div>
                <div class="profile-name">Compliance Lead</div>
                <div class="profile-role">Reviewer</div>
                <div class="profile-access">RBAC enabled · Action approval access</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if reset_clicked_global:
    reset_demo_database()
    init_db()

    st.session_state.agent_status = {}
    st.session_state.latest_result = None
    st.session_state.latest_ai = None

    st.rerun()

nav_items = [
    ("🏠 Command Center", "Command Center"),
    ("📈 Change Analysis", "Change Analysis"),
    ("📋 Action Tracker", "Action Tracker"),
    ("🕓 Version History", "Version History"),
    ("🌐 Sources", "Sources"),
    ("⚙️ Settings", "Settings"),
]

nav_cols = st.columns(6)

for col, (label, target) in zip(nav_cols, nav_items):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.page = target
            st.rerun()


# ---------------- COMMAND CENTER ----------------
if page == "Command Center":

    st.markdown("<div class='section-heading'>🤖 Agent Execution Flow</div>", unsafe_allow_html=True)

    flow_placeholder = st.empty()

    with flow_placeholder.container():
        render_agent_flow()

    if run_clicked:
        st.session_state.agent_status = {}

        with flow_placeholder.container():
            render_agent_flow(active="monitor")
        time.sleep(0.4)

        result = process_pdf_versions()
        st.session_state.latest_result = result
        set_agent("monitor", "done")

        with flow_placeholder.container():
            render_agent_flow(active="extract")
        time.sleep(0.4)
        set_agent("extract", "done")

        with flow_placeholder.container():
            render_agent_flow(active="version")
        time.sleep(0.4)
        set_agent("version", "done")

        if not result["change_detected"]:
            set_agent("analyze", "skipped")
            set_agent("impact", "skipped")
            set_agent("action", "skipped")
            set_agent("notify", "skipped")

            with flow_placeholder.container():
                render_agent_flow()

            st.info("No document-level change detected. Downstream AI agents were skipped.")

        else:
            pending_before = get_pending_actions_for_regulation(result["regulation_id"])

            if pending_before:
                st.warning(f"⚠️ {len(pending_before)} previous actions are still incomplete.")

            with flow_placeholder.container():
                render_agent_flow(active="analyze")

            ai_result = analyze_regulatory_change(result["old_text"], result["new_text"])
            st.session_state.latest_ai = ai_result
            set_agent("analyze", "done")

            with flow_placeholder.container():
                render_agent_flow(active="impact")
            time.sleep(0.4)
            set_agent("impact", "done")

            with flow_placeholder.container():
                render_agent_flow(active="action")

            save_analysis_and_actions(
                result["regulation_id"],
                ai_result,
                result["current_hash"],
            )

            set_agent("action", "done")

            with flow_placeholder.container():
                render_agent_flow(active="notify")
            time.sleep(0.4)
            set_agent("notify", "done")

            with flow_placeholder.container():
                render_agent_flow()

    result = st.session_state.latest_result
    ai_result = st.session_state.latest_ai

    render_executive_summary(ai_result, result)

    if ai_result:
        render_dashboard_insights(ai_result)


# ---------------- CHANGE ANALYSIS ----------------
elif page == "Change Analysis":

    st.markdown("## 📈 Change Analysis")

    result = st.session_state.latest_result
    ai_result = st.session_state.latest_ai

    if not result:
        st.info("Run monitor first.")
    else:
        col_old, col_new = st.columns(2)

        with col_old:
            st.subheader("Previous Version")
            st.text_area("Old Text", result["old_text"], height=320, disabled=True)

        with col_new:
            st.subheader("Latest Version")
            st.text_area("New Text", result["new_text"], height=320, disabled=True)

        st.divider()
        render_readable_ai_output(ai_result)


# ---------------- ACTION TRACKER ----------------
elif page == "Action Tracker":

    st.markdown("## 📋 Action Tracker")

    actions = get_actions()
    open_actions = [a for a in actions if a[5] != "Completed"]
    completed_actions = [a for a in actions if a[5] == "Completed"]

    tab_open, tab_done = st.tabs(["Open Actions", "Completed Actions"])

    with tab_open:
        if open_actions:
            h1, h2, h3, h4, h5 = st.columns([4, 2, 2, 2, 2])
            h1.markdown("**Action**")
            h2.markdown("**Owner**")
            h3.markdown("**Priority**")
            h4.markdown("**Due Date**")
            h5.markdown("**Status**")
            st.divider()

            for action in open_actions:
                action_id, reg_id, text, owner, priority, status, due_date, created_at, source, last_updated_at = action

                c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])

                with c1:
                    st.write(text)
                    st.caption(f"{reg_id} | {source or 'Unknown'} | Last extracted: {last_updated_at or 'N/A'}")

                with c2:
                    st.write(owner)

                with c3:
                    st.write(priority)

                with c4:
                    selected_due_date = st.date_input(
                        "Due Date",
                        value=parse_due_date(due_date),
                        key=f"due_date_{action_id}_{due_date}",
                    )

                    if str(selected_due_date) != str(due_date):
                        update_action_due_date(action_id, str(selected_due_date))
                        st.rerun()

                    render_due_date_status(selected_due_date, status)

                with c5:
                    status_options = ["Not Started", "In Progress", "Completed"]

                    if status not in status_options:
                        status = "Not Started"

                    new_status = st.selectbox(
                        "Status",
                        status_options,
                        index=status_options.index(status),
                        key=f"status_page_{action_id}_{status}",
                    )

                    if new_status != status:
                        update_action_status(action_id, new_status)
                        st.rerun()

                st.divider()
        else:
            st.success("No open actions.")

    with tab_done:
        if completed_actions:
            for action in completed_actions:
                action_id, reg_id, text, owner, priority, status, due_date, created_at, source, last_updated_at = action
                st.success(f"✅ {text}")
                st.caption(f"{reg_id} | {source or 'Unknown'} | Completed")
        else:
            st.info("No completed actions yet.")


# ---------------- VERSION HISTORY ----------------
elif page == "Version History":

    st.markdown("## 🕓 Version Timeline")

    result = st.session_state.latest_result

    if result:
        versions = get_versions_for_regulation(result["regulation_id"])

        st.info(
            "Regulation ID remains stable. Each detected update creates a new version with timestamped evidence."
        )

        if versions:
            for version in versions:
                version_number, content_hash, detected_at = version
                label = "Baseline" if version_number == 1 else "Updated"

                with st.container(border=True):
                    st.markdown(f"### v{version_number} — {label}")
                    st.write(f"Detected: {str(detected_at)[:19]}")
                    st.write("Evidence: Document fingerprint stored")
                    st.write("Verification: AI verified")

            flow = " → ".join([f"v{v[0]}" for v in versions])
            st.success(f"Change Flow: {flow}")
        else:
            st.warning("No stored version rows found yet.")
    else:
        st.info("Run monitor first to generate version history.")


# ---------------- SOURCES ----------------
elif page == "Sources":

    st.markdown("## 🌐 Real Regulatory Source Monitor")

    if st.button("Fetch Live Regulatory Sources", type="primary"):
        updates = fetch_regulatory_sources()

        st.success(f"Fetched {len(updates)} regulatory updates")

        for update in updates:
            with st.expander(f"{update['source']} | {update['title']}"):
                st.write(f"**Jurisdiction:** {update['jurisdiction']}")
                st.write(f"**Published:** {update['published']}")
                st.write(f"**Link:** {update['link']}")

                if update["is_new_update"] == 1:
                    st.error("🔴 New regulatory update detected")
                else:
                    st.success("🟢 No new update since last fetch")

                if update.get("is_fallback"):
                    st.warning("Fallback demo source used because live feed was unavailable.")


# ---------------- SETTINGS ----------------
elif page == "Settings":

    st.markdown("## ⚙️ Settings & Access Control")

    with st.container(border=True):
        st.markdown("### 👤 Logged-in User")
        st.write("Name: Compliance Lead")
        st.write("Role: Reviewer")
        st.write("Access: View dashboard, update action status, review AI recommendations")

    with st.container(border=True):
        st.markdown("### 🔐 RBAC Model")
        st.write("Admin: Configure sources and users")
        st.write("Compliance Lead: Review risks and approve actions")
        st.write("Team Owner: Update assigned actions")
        st.write("Auditor: Read-only access to version history and action logs")


st.markdown(
    "<div class='footer-center'>LexaFlow AI © 2026 | Built with Azure AI | WoltersKluwer AgenticCodeGames</div>",
    unsafe_allow_html=True,
)