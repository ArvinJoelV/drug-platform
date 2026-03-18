import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


def build_output_path(molecule: str, output: str | None) -> Path:
    if output:
        return Path(output)

    safe_name = molecule.strip().lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"{safe_name}_orchestrator_{timestamp}.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call the orchestrator and save the full response to a JSON file."
    )
    parser.add_argument(
        "--molecule",
        default="Aspirin",
        help="Molecule name to send to the orchestrator.",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/orchestrate",
        help="Orchestrator endpoint URL.",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON path. If omitted, a timestamped file is created in ./outputs.",
    )
    args = parser.parse_args()

    payload = {"molecule": args.molecule}
    output_path = build_output_path(args.molecule, args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Calling orchestrator at: {args.url}")
    print(f"Payload: {payload}")

    try:
        response = requests.post(
            args.url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return 1

    try:
        response_json = response.json()
    except ValueError:
        print("Response was not valid JSON.")
        return 1

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(response_json, handle, indent=2, ensure_ascii=False)

    print(f"Saved response to: {output_path}")
    print("Top-level keys:", ", ".join(response_json.keys()))

    agents = response_json.get("agents", {})
    if isinstance(agents, dict) and agents:
        print("Agents captured:", ", ".join(agents.keys()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
