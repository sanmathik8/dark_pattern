"""
Single Scenario Runner CLI
Runs a single scenario by ID across Dark and Clean variants.
"""

import sys
import json
import argparse
from pathlib import Path

SIMULATOR_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SIMULATOR_DIR.parent))

from simulator.core.runner import UniversalScenarioRunner, ScenarioContract
from simulator.evaluation.evaluator import UniversalScenarioEvaluator

SIMULATOR_DIR = Path(__file__).parent.parent
MANIFEST_PATH = SIMULATOR_DIR / "manifest.json"

def run_single_scenario(scenario_id: int, variant: str = "dark"):
    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Manifest file not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    sc_data = next((s for s in manifest.get("scenarios", []) if s["id"] == scenario_id), None)
    if not sc_data:
        print(f"[ERROR] Scenario ID {scenario_id} not found in manifest.")
        return

    scenario = ScenarioContract(
        id=sc_data["id"],
        name=sc_data["title"],
        source=sc_data.get("github_repo", ""),
        start_command="python simulator/run_scenarios.py",
        url=sc_data["variant_urls"][variant],
        dark_variant=sc_data["variant_urls"]["dark"],
        clean_variant=sc_data["variant_urls"]["clean"],
        ground_truth={
            "scenario_id": sc_data["id"],
            "planted_patterns": sc_data["dark_patterns"]
        }
    )

    runner = UniversalScenarioRunner()
    result = runner.run_scenario_variant(scenario, variant=variant)

    evaluator = UniversalScenarioEvaluator()
    eval_res = evaluator.evaluate_suite([result])

    print(f"\n--- Scenario #{scenario_id} [{scenario.name}] Variant={variant.upper()} ---")
    print(f"Target URL : {result['target_url']}")
    print(f"Findings   : {json.dumps(result['findings'], indent=2)}")
    print(f"Status     : {eval_res['evaluations'][0]['status']}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run single dark pattern scenario")
    parser.add_argument("--id", type=int, default=1, help="Scenario ID (1-14)")
    parser.add_argument("--variant", type=str, default="dark", choices=["dark", "clean"], help="Scenario variant")
    args = parser.parse_args()
    
    run_single_scenario(args.id, args.variant)
