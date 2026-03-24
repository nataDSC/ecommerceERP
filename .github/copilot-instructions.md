# Agent Instructions

**Act as an AI Agent Architect specializing in tool-calling and autonomous reasoning.** Your task is to design a multi-agent system for inventory management in e-commerce. The agent should be able to analyze internal sales data, research market trends, and generate restock strategies autonomously.

## Architectural Constraints for the Project

1. **Pattern:** Implement a _Plan-Act-Reflect_ loop. The agent must first generate a _Plan_ (list of sub-tasks), then execute tools, and finally reflect on whether the observations satisfy the original goal.
2. **State Management:** Use a structured _State_ object (or a TypedDict if using LangGraph) to track: `inventory_data`, `market_competitor_data`, `reasoning_steps`, and `final_recommendation`.
3. **Modularity:** Decouple the _Tools_ (API wrappers) from the _Orchestrator_ (the logic loop). Tools should return structured JSON, not raw text.
4. **Observability:** Every "Thought" and "Action" must be logged to a `reasoning_trace.log` file so we can audit the agent's decision-making process.
5. **Validation:** Include a "Cost-Guard" middleware that prevents the agent from making more than 5 tool calls per cycle to avoid infinite loops and token drain.

# The Prompt

Build an autonomous agent loop for inventory management.

1. The State Machine: Implement a loop that maintains a 'Reasoning Trace' (a list of thoughts and observations).
2. Tools: Define two tools as Python functions:
   - `get_inventory_stats(sku)` which returns mock stock/lead-time data,
   - `fetch_market_research(product_name)` which uses the Tavily API to get current competitor pricing.
3. The Loop: The agent should check internal inventory first. If stock is <20%, it must autonomously decide to call the market research tool before generating a restock recommendation.
4. Output: The final output must be a 'Structured Proposal' explaining the mathematical rationale (Velocity vs. Lead Time) and the market-aware adjustment.
