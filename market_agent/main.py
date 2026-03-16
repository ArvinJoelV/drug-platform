"""CLI entry point for the Market Intelligence Agent prototype."""

from __future__ import annotations

import argparse
import json

from market_agent.market_agent import MarketIntelligenceAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Naive RAG market intelligence prototype")
    parser.add_argument("--disease", required=True, help="Disease name, for example 'colorectal cancer'")
    parser.add_argument(
        "--prevalence-csv",
        default=None,
        help="Optional local CSV with disease prevalence or incidence rows",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model name to use when OPENAI_API_KEY is set",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    agent = MarketIntelligenceAgent()
    result = agent.analyze_disease(
        disease_name=args.disease,
        prevalence_csv_path=args.prevalence_csv,
        model=args.model,
    )

    print("Market Opportunity Analysis:")
    print(result["market_summary"])
    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

