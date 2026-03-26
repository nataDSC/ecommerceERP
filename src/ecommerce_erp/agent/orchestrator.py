from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from ecommerce_erp.agent.guardrails import CostGuardError, check_cost_guard
from ecommerce_erp.agent.state import AgentState, ApprovalStatus, Phase, ReasoningStep
from ecommerce_erp.recommendation.engine import compute_restock
from ecommerce_erp.tools.inventory import get_inventory_stats
from ecommerce_erp.tools.market import fetch_market_research
from ecommerce_erp.utils.trace_logger import log_event

_LOW_STOCK_THRESHOLD = 20.0  # percent — triggers mandatory market research


# ---------------------------------------------------------------------------
# Helper: create a ReasoningStep and write it to the trace log atomically
# ---------------------------------------------------------------------------

def _make_step(
    phase: str,
    thought: str,
    action: str | None = None,
    observation: str | None = None,
    tool_call_count: int = 0,
    metadata: dict[str, Any] | None = None,
) -> ReasoningStep:
    log_event(
        phase=phase,
        thought=thought,
        action=action,
        observation=observation,
        metadata=metadata,
    )
    return ReasoningStep(
        phase=phase,
        thought=thought,
        action=action,
        observation=observation,
        tool_call_count=tool_call_count,
    )


# ---------------------------------------------------------------------------
# Node: PLAN
# Decides the next sub-task based on what data is currently in state.
# ---------------------------------------------------------------------------

def plan_node(state: AgentState) -> dict[str, Any]:
    inventory = state.get("inventory_data")
    market = state.get("market_competitor_data")
    error = state.get("error")

    if error:
        thought = f"[PLAN] Error in prior step: '{error}'. Halting agent loop."
        step = _make_step(Phase.PLAN.value, thought)
        return {
            "plan": [],
            "current_phase": Phase.PLAN.value,
            "reasoning_steps": [step],
            "goal_satisfied": True,
        }

    if inventory is None:
        new_plan = ["call_inventory_tool"]
        thought = (
            f"[PLAN] No inventory data found for SKU '{state['sku']}'. "
            "Sub-task 1: Call get_inventory_stats() to retrieve current stock, "
            "daily velocity, and supplier lead time from the ERP system."
        )

    elif not inventory.get("found", True):
        thought = (
            f"[PLAN] SKU '{state['sku']}' does not exist in the ERP system. "
            "Cannot proceed — terminating loop."
        )
        step = _make_step(Phase.PLAN.value, thought)
        return {
            "plan": [],
            "current_phase": Phase.PLAN.value,
            "reasoning_steps": [step],
            "error": inventory.get("error", f"SKU '{state['sku']}' not found."),
            "goal_satisfied": True,
        }

    elif inventory.get("stock_pct", 100.0) < _LOW_STOCK_THRESHOLD and market is None:
        new_plan = ["call_market_research_tool"]
        thought = (
            f"[PLAN] Stock level is {inventory['stock_pct']}% — below the critical "
            f"{_LOW_STOCK_THRESHOLD}% threshold. Market intelligence is required before "
            "generating a restock recommendation. "
            "Sub-task 2: Call fetch_market_research() to obtain competitor pricing "
            "and demand signals."
        )

    else:
        new_plan = ["generate_recommendation"]
        stock_ctx = f"{inventory.get('stock_pct')}% stock"
        mkt_ctx = "with market data" if market else "without market data (stock is healthy)"
        thought = (
            f"[PLAN] All required data is available ({stock_ctx}, {mkt_ctx}). "
            "Final sub-task: Apply the Safety Stock formula and generate the "
            "structured restock proposal."
        )

    step = _make_step(Phase.PLAN.value, thought, action=f"Queued sub-tasks: {new_plan}")
    return {
        "plan": new_plan,
        "current_phase": Phase.PLAN.value,
        "reasoning_steps": [step],
    }


# ---------------------------------------------------------------------------
# Node: ACT
# Executes the first sub-task in the plan and updates state with results.
# ---------------------------------------------------------------------------

def act_node(state: AgentState) -> dict[str, Any]:
    plan = state.get("plan", [])
    if not plan:
        return {"current_phase": Phase.ACT.value}

    task = plan[0]
    call_count = state.get("tool_calls_this_cycle", 0)
    updates: dict[str, Any] = {"current_phase": Phase.ACT.value}

    # Cost-guard: only counts against external tool invocations
    if task in ("call_inventory_tool", "call_market_research_tool"):
        try:
            check_cost_guard(state)
        except CostGuardError as exc:
            msg = str(exc)
            step = _make_step(Phase.ACT.value, msg)
            return {
                "current_phase": Phase.ACT.value,
                "error": msg,
                "goal_satisfied": True,
                "reasoning_steps": [step],
            }

    # ------------------------------------------------------------------
    if task == "call_inventory_tool":
        sku = state["sku"]
        thought = f"[ACT] Invoking tool: get_inventory_stats(sku='{sku}')"
        result = get_inventory_stats(sku)
        call_count += 1
        if result.get("found"):
            obs = (
                f"stock_pct={result.get('stock_pct')}%  |  "
                f"current_stock={result.get('current_stock')} units  |  "
                f"daily_velocity={result.get('daily_velocity')} units/day  |  "
                f"lead_time_days={result.get('lead_time_days')} days"
            )
        else:
            obs = f"SKU not found: {result.get('error')}"
        step = _make_step(
            Phase.ACT.value, thought,
            action="get_inventory_stats",
            observation=obs,
            tool_call_count=call_count,
        )
        updates["inventory_data"] = result
        updates["tool_calls_this_cycle"] = call_count

    # ------------------------------------------------------------------
    elif task == "call_market_research_tool":
        product_name = state["inventory_data"]["product_name"]
        thought = f"[ACT] Invoking tool: fetch_market_research(product_name='{product_name}')"
        result = fetch_market_research(product_name)
        call_count += 1
        obs = (
            f"demand_signal={result.get('demand_signal')}  |  "
            f"price_trend={result.get('price_trend')}  |  "
            f"market_avg_price=${result.get('market_avg_price')}  |  "
            f"source={result.get('source')}"
        )
        step = _make_step(
            Phase.ACT.value, thought,
            action="fetch_market_research",
            observation=obs,
            tool_call_count=call_count,
        )
        updates["market_competitor_data"] = result
        updates["tool_calls_this_cycle"] = call_count

    # ------------------------------------------------------------------
    elif task == "generate_recommendation":
        thought = (
            "[ACT] Computing restock recommendation via Safety Stock formula: "
            "ReorderPoint = (LeadTime × AverageDailyUsage) + SafetyStock, "
            "where SafetyStock = 20% of LeadTimeDemand."
        )
        proposal = compute_restock(state["inventory_data"], state.get("market_competitor_data"))
        sku = state["sku"]
        approval_msg = f"ACTION REQUIRED: Awaiting Human Approval for SKU {sku}."
        obs = (
            f"Proposal generated — action={proposal['json']['recommendation']}, "
            f"restock_qty={proposal['json']['restock_quantity']} units. {approval_msg}"
        )
        step = _make_step(
            Phase.ACT.value, thought,
            action="compute_restock",
            observation=obs,
            tool_call_count=call_count,
            metadata={"sku": sku, "requires_approval": True},
        )
        # Emit the human-in-the-loop pause signal to stdout and the trace log
        log_event(
            phase=Phase.ACT.value,
            thought=approval_msg,
            action="human_in_the_loop",
            observation=approval_msg,
            metadata={"sku": sku, "approval_status": ApprovalStatus.PENDING_APPROVAL.value},
        )
        print(f"\n{'─' * 64}")
        print(f"⚠️  {approval_msg}")
        print(f"{'─' * 64}\n")
        updates["final_recommendation"] = proposal
        updates["approval_status"] = ApprovalStatus.PENDING_APPROVAL.value

    else:
        thought = f"[ACT] Unknown task '{task}' in plan. Skipping."
        step = _make_step(Phase.ACT.value, thought)

    updates["reasoning_steps"] = [step]
    return updates


# ---------------------------------------------------------------------------
# Node: REFLECT
# Evaluates whether the goal has been satisfied and decides whether to loop.
# ---------------------------------------------------------------------------

def reflect_node(state: AgentState) -> dict[str, Any]:
    final = state.get("final_recommendation")
    error = state.get("error")

    if error:
        thought = (
            f"[REFLECT] Error state detected: '{error}'. "
            "Terminating agent loop — no recommendation can be generated."
        )
        goal_satisfied = True

    elif final is not None:
        qty = final["json"]["restock_quantity"]
        action = final["json"]["recommendation"]
        thought = (
            f"[REFLECT] Goal satisfied. Recommendation: {action} — {qty} units for "
            f"SKU '{state['sku']}'. "
            f"Total tool calls this cycle: {state.get('tool_calls_this_cycle', 0)}. "
            f"Approval status: {state.get('approval_status')}."
        )
        goal_satisfied = True

    else:
        inv_status = "present" if state.get("inventory_data") else "missing"
        mkt_status = "present" if state.get("market_competitor_data") else "not yet fetched"
        thought = (
            f"[REFLECT] Loop iteration complete. "
            f"inventory_data={inv_status}, market_data={mkt_status}. "
            f"Tool calls so far: {state.get('tool_calls_this_cycle', 0)}. "
            "Goal not yet satisfied — returning to PLAN phase."
        )
        goal_satisfied = False

    step = _make_step(Phase.REFLECT.value, thought)
    return {
        "current_phase": Phase.DONE.value if goal_satisfied else Phase.REFLECT.value,
        "goal_satisfied": goal_satisfied,
        "reasoning_steps": [step],
    }


# ---------------------------------------------------------------------------
# Routing function
# ---------------------------------------------------------------------------

def _route_after_reflect(state: AgentState) -> str:
    return END if state.get("goal_satisfied", False) else "plan"


def approval_node(state: AgentState) -> dict[str, Any]:
    """
    Pause execution for human approval when a recommendation is available.

    Uses LangGraph's interrupt() so the graph thread can be resumed later
    via Command(resume="APPROVED"|"REJECTED") from the UI.
    """
    recommendation = state.get("final_recommendation")
    if recommendation is None:
        return {"current_phase": Phase.ACT.value}

    status = str(state.get("approval_status", ApprovalStatus.PENDING_APPROVAL.value))
    if status in (ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value):
        return {"current_phase": Phase.ACT.value}

    sku = state.get("sku", "UNKNOWN")
    decision = interrupt(
        {
            "type": "approval_required",
            "message": f"ACTION REQUIRED: Awaiting Human Approval for SKU {sku}.",
            "sku": sku,
            "allowed_decisions": [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value],
        }
    )

    normalized = str(decision).strip().upper()
    if normalized not in (ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value):
        normalized = ApprovalStatus.REJECTED.value

    thought = f"[APPROVAL] Human decision received for SKU '{sku}': {normalized}."
    step = _make_step(
        Phase.ACT.value,
        thought,
        action="human_approval_signal",
        observation=f"approval_status={normalized}",
        metadata={"sku": sku, "approval_status": normalized},
    )

    updated_recommendation = recommendation
    if isinstance(recommendation, dict):
        json_block = dict(recommendation.get("json", {}))
        json_block["approval_status"] = normalized
        markdown_block = recommendation.get("markdown")
        if isinstance(markdown_block, str):
            updated_markdown = markdown_block.replace(
                "| **Approval Status** | PENDING_APPROVAL |",
                f"| **Approval Status** | {normalized} |",
            )
            if normalized == ApprovalStatus.APPROVED.value:
                updated_markdown = updated_markdown.replace(
                    "\n> ⚠️ **ACTION REQUIRED: Awaiting Human Approval.**  This proposal must be reviewed and approved before any purchase order is placed.",
                    "\n> ✅ **APPROVED:** Human review completed. This proposal is approved.",
                )
            else:
                updated_markdown = updated_markdown.replace(
                    "\n> ⚠️ **ACTION REQUIRED: Awaiting Human Approval.**  This proposal must be reviewed and approved before any purchase order is placed.",
                    "\n> ❌ **REJECTED:** Human review rejected this proposal. No purchase order should be placed.",
                )
            updated_recommendation = {
                **recommendation,
                "json": json_block,
                "markdown": updated_markdown,
            }
        else:
            updated_recommendation = {**recommendation, "json": json_block}

    return {
        "approval_status": normalized,
        "final_recommendation": updated_recommendation,
        "reasoning_steps": [step],
        "current_phase": Phase.ACT.value,
    }


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph(*, human_in_the_loop: bool = False) -> Any:
    """
    Compile and return the LangGraph StateGraph implementing the
    Plan → Act → Reflect loop for inventory management.
    """
    graph: StateGraph = StateGraph(AgentState)

    graph.add_node("plan", plan_node)
    graph.add_node("act", act_node)
    graph.add_node("reflect", reflect_node)
    if human_in_the_loop:
        graph.add_node("approval", approval_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "act")
    if human_in_the_loop:
        graph.add_edge("act", "approval")
        graph.add_edge("approval", "reflect")
    else:
        graph.add_edge("act", "reflect")
    graph.add_conditional_edges(
        "reflect",
        _route_after_reflect,
        {"plan": "plan", END: END},
    )

    if human_in_the_loop:
        return graph.compile(checkpointer=MemorySaver())
    return graph.compile()


def make_initial_state(sku: str) -> dict[str, Any]:
    """Return a fresh initial state dict for a new agent run."""
    return {
        "sku": sku,
        "inventory_data": None,
        "market_competitor_data": None,
        "reasoning_steps": [],
        "final_recommendation": None,
        "approval_status": ApprovalStatus.PENDING_APPROVAL.value,
        "tool_calls_this_cycle": 0,
        "plan": [],
        "current_phase": Phase.PLAN.value,
        "goal_satisfied": False,
        "error": None,
    }
