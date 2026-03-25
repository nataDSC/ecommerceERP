from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from ecommerce_erp.agent.orchestrator import build_graph, make_initial_state

load_dotenv()

st.set_page_config(
    page_title="Ecommerce ERP Inventory Agent",
    page_icon="📦",
    layout="wide",
)


def _init_session_state() -> None:
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
    if "trace_steps" not in st.session_state:
        st.session_state.trace_steps = []
    if "approval_decision" not in st.session_state:
        st.session_state.approval_decision = None
    if "run_metadata" not in st.session_state:
        st.session_state.run_metadata = None
    if "graph" not in st.session_state:
        st.session_state.graph = None
    if "graph_config" not in st.session_state:
        st.session_state.graph_config = None
    if "awaiting_approval" not in st.session_state:
        st.session_state.awaiting_approval = False
    if "interrupt_payload" not in st.session_state:
        st.session_state.interrupt_payload = None


def _badge_for_phase(phase: str) -> str:
    if phase == "PLAN":
        return "🧠 PLAN"
    if phase == "ACT":
        return "⚙️ ACT"
    if phase == "REFLECT":
        return "🔍 REFLECT"
    return phase


def _render_trace(steps: list[dict[str, Any]]) -> None:
    st.subheader("Reasoning Trace")
    if not steps:
        st.info("Run an analysis to see Plan → Act → Reflect steps.")
        return

    for i, step in enumerate(steps, start=1):
        phase = _badge_for_phase(str(step.get("phase", "UNKNOWN")))
        thought = str(step.get("thought", ""))
        action = step.get("action")
        observation = step.get("observation")
        tool_calls = step.get("tool_call_count", 0)

        with st.expander(f"{i}. {phase}", expanded=i == len(steps)):
            st.markdown(f"**Thought**: {thought}")
            if action:
                st.markdown(f"**Action**: {action}")
            if observation:
                st.markdown(f"**Observation**: {observation}")
            st.caption(f"Tool calls used so far: {tool_calls}")


def _render_graph_status_badge(result: dict[str, Any]) -> None:
    """Render a clear paused/resumed status indicator for the approval workflow."""
    latest_status = str(result.get("approval_status", "N/A"))
    if st.session_state.awaiting_approval:
        st.warning("Graph Status: PAUSED - Awaiting Human Approval")
    elif latest_status in ("APPROVED", "REJECTED"):
        st.success(f"Graph Status: RESUMED - Decision Applied ({latest_status})")
    else:
        st.info("Graph Status: RUNNING / READY")


def _proposal_markdown_for_display(markdown_text: str, hide_action_required: bool) -> str:
    """
    Hide the hardcoded pending-approval callout in markdown after a decision
    to avoid confusing stale messaging in the UI.
    """
    if not hide_action_required:
        return markdown_text

    filtered_lines: list[str] = []
    for line in markdown_text.splitlines():
        normalized = line.strip().upper()
        if "ACTION REQUIRED" in normalized:
            continue
        if "THIS PROPOSAL MUST BE REVIEWED AND APPROVED" in normalized:
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)


def _inject_sidebar_button_theme() -> None:
    """Apply a custom navy style to the sidebar primary button (Run analysis)."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background-color: #04143a;
            border: 2px solid #9ec5ff;
            color: #ffffff;
            font-weight: 700;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {
            background-color: #0a2f84;
            border-color: #d7e7ff;
            color: #ffffff;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"]:focus {
            box-shadow: 0 0 0 0.25rem rgba(255, 215, 0, 0.45);
            outline: none;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"]:disabled {
            background-color: #5e6d8f;
            border-color: #c9d3e6;
            color: #f5f7fb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _market_call_summary(result: dict[str, Any]) -> tuple[str, str]:
    """
    Return (source, status) for the most recent market research call.

    source examples: mock, tavily_live, n/a
    status examples: success, not_called, error: <message>
    """
    market_data = result.get("market_competitor_data")
    if not market_data:
        return "n/a", "not_called"

    source = str(market_data.get("source", "unknown"))
    found = bool(market_data.get("found", False))
    if found:
        return source, "success"

    err = str(market_data.get("error", "unknown error"))
    if len(err) > 120:
        err = err[:117] + "..."
    return source, f"error: {err}"


def _run_agent(sku: str, use_mock: bool) -> dict[str, Any]:
    os.environ["TAVILY_MOCK"] = "true" if use_mock else "false"

    graph = build_graph(human_in_the_loop=True)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(make_initial_state(sku), config=config)

    st.session_state.graph = graph
    st.session_state.graph_config = config
    st.session_state.trace_steps = list(result.get("reasoning_steps", []))
    st.session_state.awaiting_approval = "__interrupt__" in result
    st.session_state.interrupt_payload = result.get("__interrupt__")
    return result


def _resume_with_decision(decision: str) -> dict[str, Any] | None:
    graph = st.session_state.graph
    config = st.session_state.graph_config
    if graph is None or config is None:
        st.error("No active approval session. Run analysis first.")
        return None

    result = graph.invoke(Command(resume=decision), config=config)
    st.session_state.trace_steps = list(result.get("reasoning_steps", []))
    st.session_state.awaiting_approval = "__interrupt__" in result
    st.session_state.interrupt_payload = result.get("__interrupt__")
    return result


def _render_results() -> None:
    result = st.session_state.latest_result
    if not result:
        return

    if result.get("error"):
        st.error(f"Agent ended with error: {result['error']}")
        return

    proposal = result.get("final_recommendation")
    if not proposal:
        st.warning("No recommendation produced.")
        return

    _render_graph_status_badge(result)

    st.subheader("Restock Proposal")
    tab_md, tab_json = st.tabs(["Markdown", "JSON"])

    latest_status = str(proposal["json"].get("approval_status", "PENDING_APPROVAL"))
    hide_action_required = latest_status in ("APPROVED", "REJECTED")
    markdown_to_display = _proposal_markdown_for_display(
        proposal["markdown"], hide_action_required=hide_action_required
    )

    with tab_md:
        st.markdown(markdown_to_display)

    with tab_json:
        st.json(proposal["json"])

    if st.session_state.awaiting_approval and st.session_state.interrupt_payload:
        st.warning(
            f"ACTION REQUIRED: Awaiting Human Approval for SKU {result.get('sku', 'N/A')}."
        )
        st.info("Graph execution is paused waiting for human approval.")
    elif latest_status == "APPROVED":
        st.success("Approval completed. The graph resumed and applied APPROVED status.")
    elif latest_status == "REJECTED":
        st.info("Decision recorded as REJECTED. The graph resumed and applied REJECTED status.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Approve",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.awaiting_approval,
        ):
            resumed = _resume_with_decision("APPROVED")
            if resumed is not None:
                st.session_state.latest_result = resumed
            st.session_state.approval_decision = "APPROVED"
            st.rerun()
    with col2:
        if st.button(
            "Reject",
            use_container_width=True,
            disabled=not st.session_state.awaiting_approval,
        ):
            resumed = _resume_with_decision("REJECTED")
            if resumed is not None:
                st.session_state.latest_result = resumed
            st.session_state.approval_decision = "REJECTED"
            st.rerun()

    decision = st.session_state.approval_decision
    if decision:
        st.success(f"Decision recorded: {decision}")

    latest_status = proposal["json"].get("approval_status")
    if latest_status in ("APPROVED", "REJECTED"):
        st.caption(f"Final approval status in graph state: {latest_status}")


def main() -> None:
    _init_session_state()
    _inject_sidebar_button_theme()

    st.title("Ecommerce ERP Inventory Agent")
    st.caption("Phase 1 demo: public Streamlit UI for Plan → Act → Reflect")

    with st.sidebar:
        st.header("Run Controls")
        sku = st.selectbox(
            "SKU",
            options=["SKU-001", "SKU-002", "SKU-003", "SKU-004", "SKU-005"],
            index=0,
        )
        use_mock = st.toggle("Use mock market data", value=True)
        run_clicked = st.button("Run analysis", type="primary", use_container_width=True)

        st.divider()
        st.caption("Demo mode is intended for public access.")
        st.caption("For production, add auth (basic auth or OAuth) in Phase 2+.")

    if run_clicked:
        st.session_state.approval_decision = None
        st.session_state.awaiting_approval = False
        st.session_state.interrupt_payload = None
        st.session_state.run_metadata = {
            "sku": sku,
            "mock": use_mock,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        with st.spinner("Running agent loop..."):
            st.session_state.latest_result = _run_agent(sku=sku, use_mock=use_mock)

    left, right = st.columns([1.1, 1.4])
    with left:
        st.subheader("Run Summary")
        meta = st.session_state.run_metadata
        if meta:
            st.write(meta)
        else:
            st.info("No run yet.")

        result = st.session_state.latest_result
        if result:
            st.metric("Tool Calls This Cycle", result.get("tool_calls_this_cycle", 0))
            st.metric("Goal Satisfied", "Yes" if result.get("goal_satisfied") else "No")
            st.metric("Approval Status", str(result.get("approval_status", "N/A")))

            source, market_status = _market_call_summary(result)
            st.markdown(f"**Market Source:** {source}")
            st.markdown(f"**Last Market Call Status:** {market_status}")

    with right:
        _render_trace(st.session_state.trace_steps)

    st.divider()
    _render_results()

    st.divider()
    st.caption("Trace log file: logs/reasoning_trace.log")
    st.caption("CLI still available: ecommerce-erp --sku SKU-001")


if __name__ == "__main__":
    main()
