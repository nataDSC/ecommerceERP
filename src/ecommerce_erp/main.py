def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()  # load .env before anything else reads env vars

    import argparse
    import json

    from ecommerce_erp.agent.orchestrator import build_graph, make_initial_state

    parser = argparse.ArgumentParser(
        description="Autonomous Inventory Management Agent (Plan-Act-Reflect)"
    )
    parser.add_argument(
        "--sku",
        default="SKU-001",
        help="SKU to analyse (default: SKU-001). Available mock SKUs: SKU-001 … SKU-005",
    )
    args = parser.parse_args()

    print(f"Starting inventory agent for SKU: {args.sku}")
    print("─" * 64)

    graph = build_graph()
    result = graph.invoke(make_initial_state(args.sku))

    if result.get("error"):
        print(f"\n[ERROR] {result['error']}")
        return 1

    recommendation = result.get("final_recommendation")
    if recommendation:
        print(recommendation["markdown"])
        print("\n--- JSON Proposal ---")
        print(json.dumps(recommendation["json"], indent=2))
        print(f"\nReasoning steps recorded: {len(result.get('reasoning_steps', []))}")
    else:
        print("No recommendation generated.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
