import os
from datetime import date, datetime, timedelta
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="LexaFlow AI v2", page_icon="⚖️", layout="wide")


API_BASE = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api/v1")
DEFAULT_TIMEOUT = 45


def api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict[str, Any] | None = None, params: dict[str, Any] | None = None) -> Any:
    response = requests.post(
        f"{API_BASE}{path}",
        json=payload,
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def api_patch(path: str, payload: dict[str, Any]) -> Any:
    response = requests.patch(f"{API_BASE}{path}", json=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def parse_due_date(value: str) -> date:
    try:
        if "days" in value:
            days = int(value.split()[0])
            return date.today() + timedelta(days=days)
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date.today() + timedelta(days=7)


if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "latest_analysis" not in st.session_state:
    st.session_state.latest_analysis = None


st.title("⚖️ LexaFlow AI v2")
st.caption("Autonomous Regulatory Intelligence Command Center")

top1, top2, top3 = st.columns([1.5, 1.2, 1.2])
with top1:
    run_clicked = st.button("▶ Run Monitor", type="primary", use_container_width=True)
with top2:
    fetch_sources_clicked = st.button("🌐 Fetch Sources", use_container_width=True)
with top3:
    reset_clicked = st.button("🔄 Reset Demo DB", use_container_width=True)

if run_clicked:
    with st.spinner("Running monitor pipeline..."):
        try:
            result = api_post("/monitor/run")
            st.session_state.latest_result = result
            st.session_state.latest_analysis = result.get("analysis")
            st.success("Monitor run completed.")
        except Exception as exc:
            st.error(f"Monitor run failed: {exc}")

if fetch_sources_clicked:
    with st.spinner("Fetching regulatory sources..."):
        try:
            updates = api_post("/sources/fetch")
            st.success(f"Fetched {len(updates)} updates")
        except Exception as exc:
            st.error(f"Source fetch failed: {exc}")

if reset_clicked:
    try:
        api_post("/admin/reset")
        st.session_state.latest_result = None
        st.session_state.latest_analysis = None
        st.success("Demo database reset.")
    except Exception as exc:
        st.error(f"Reset failed: {exc}")

nav = st.radio(
    "Navigation",
    ["Command Center", "Change Analysis", "Action Tracker", "Version History", "Sources", "Settings"],
    horizontal=True,
    label_visibility="collapsed",
)

try:
    summary = api_get("/dashboard/summary")
except Exception:
    summary = {
        "regulations_monitored": 0,
        "source_updates": 0,
        "high_risk_count": 0,
        "pending_actions": 0,
    }

s1, s2, s3, s4 = st.columns(4)
s1.metric("Regulations Monitored", summary["regulations_monitored"])
s2.metric("New Source Updates", summary["source_updates"])
s3.metric("High Risk Analyses", summary["high_risk_count"])
s4.metric("Pending Actions", summary["pending_actions"])

st.divider()

if nav == "Command Center":
    result = st.session_state.latest_result
    analysis = st.session_state.latest_analysis

    if result is None:
        st.info("Run monitor to generate the latest version intelligence.")
    else:
        left, right = st.columns(2)
        with left:
            st.subheader("Run Output")
            st.json(
                {
                    "regulation_id": result["regulation_id"],
                    "change_detected": result["change_detected"],
                    "old_version": result["old_version"],
                    "new_version": result["new_version"],
                    "carryover_open_actions": result.get("carryover_open_actions", 0),
                }
            )
        with right:
            st.subheader("Analysis Overview")
            if analysis:
                st.write(f"Risk Level: **{analysis.get('risk_level', 'unknown').title()}**")
                st.write(f"Confidence: **{int(float(analysis.get('confidence_score', 0)) * 100)}%**")
                st.write(f"Affected Teams: {', '.join(analysis.get('affected_teams', []))}")
            else:
                st.info("No analysis generated because no new change was detected.")

if nav == "Change Analysis":
    result = st.session_state.latest_result
    analysis = st.session_state.latest_analysis

    if result is None:
        st.info("Run monitor first.")
    else:
        old_col, new_col = st.columns(2)
        with old_col:
            st.subheader("Previous Version")
            st.text_area("Old Text", result["old_text"], height=300, disabled=True)
        with new_col:
            st.subheader("Latest Version")
            st.text_area("New Text", result["new_text"], height=300, disabled=True)

        st.subheader("Structured Change Analysis")
        if analysis:
            st.json(analysis)
        else:
            st.warning("No change analysis available for this run.")

if nav == "Action Tracker":
    try:
        open_actions = api_get("/actions", params={"status": "open"})
        completed_actions = api_get("/actions", params={"status": "completed"})
    except Exception as exc:
        st.error(f"Failed to load actions: {exc}")
        open_actions = []
        completed_actions = []

    tab_open, tab_done = st.tabs(["Open Actions", "Completed Actions"])

    with tab_open:
        if not open_actions:
            st.success("No open actions.")
        else:
            for action in open_actions:
                with st.container(border=True):
                    st.markdown(f"**{action['action_text']}**")
                    st.caption(
                        f"{action['regulation_id']} | {action.get('source') or 'Unknown'} | Last updated: {action.get('last_updated_at') or 'N/A'}"
                    )

                    c1, c2, c3 = st.columns([1.2, 1.2, 1.8])
                    with c1:
                        new_status = st.selectbox(
                            "Status",
                            ["Not Started", "In Progress", "Completed"],
                            index=["Not Started", "In Progress", "Completed"].index(action["status"])
                            if action["status"] in ["Not Started", "In Progress", "Completed"]
                            else 0,
                            key=f"status_{action['action_id']}",
                        )

                    with c2:
                        new_due = st.date_input(
                            "Due Date",
                            value=parse_due_date(action["due_date"]),
                            key=f"due_{action['action_id']}",
                        )

                    with c3:
                        st.write(f"Owner: **{action['owner']}**")
                        st.write(f"Priority: **{action['priority']}**")
                        if st.button("Save Update", key=f"save_{action['action_id']}"):
                            try:
                                api_patch(
                                    f"/actions/{action['action_id']}",
                                    {"status": new_status, "due_date": str(new_due)},
                                )
                                st.success("Action updated.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Update failed: {exc}")

    with tab_done:
        if not completed_actions:
            st.info("No completed actions yet.")
        else:
            for action in completed_actions:
                st.success(f"✅ {action['action_text']}")
                st.caption(
                    f"{action['regulation_id']} | Owner: {action['owner']} | Completed"
                )

if nav == "Version History":
    try:
        regulation = api_get("/regulations/current")
        versions = api_get(f"/versions/{regulation['regulation_id']}")
    except Exception as exc:
        st.error(f"Failed to load versions: {exc}")
        regulation = None
        versions = []

    if regulation:
        st.write(f"Regulation: **{regulation['title']}**")
        st.caption(
            f"{regulation['source']} | {regulation['jurisdiction']} | Status: {regulation['status']}"
        )

    if not versions:
        st.info("No versions stored yet. Run monitor first.")
    else:
        for version in versions:
            with st.container(border=True):
                st.write(f"Version: **v{version['version_number']}**")
                st.write(f"Hash: `{version['content_hash'][:16]}...`")
                st.write(f"Detected: {version['detected_at']}")

if nav == "Sources":
    try:
        recent = api_get("/sources/recent", params={"limit": 30})
    except Exception as exc:
        st.error(f"Failed to load sources: {exc}")
        recent = []

    if not recent:
        st.info("No source updates yet. Click Fetch Sources.")
    else:
        for item in recent:
            with st.expander(f"{item['source']} | {item['title']}"):
                st.write(f"Jurisdiction: **{item['jurisdiction']}**")
                st.write(f"Published: **{item['published']}**")
                st.write(f"Link: {item['link']}")
                st.write(f"Fetched At: {item['fetched_at']}")
                if item["is_new_update"]:
                    st.warning("New update detected")
                else:
                    st.success("Already seen update")
                if item["is_fallback"]:
                    st.info("Fallback source entry")

if nav == "Settings":
    st.subheader("Runtime Configuration")
    st.code(
        f"API Base URL: {API_BASE}\n"
        f"Tip: set BACKEND_API_URL in .env if your backend runs on another host.",
        language="text",
    )

st.caption("LexaFlow AI v2 | FastAPI + Streamlit")

