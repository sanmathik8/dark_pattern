"""
Batch Scenario Runner CLI
Runs all 14 scenarios across Dark and Clean variants using the Universal Scenario Orchestrator.
Evaluates results using Ground-Truth Behavioral Predicates and saves output to results/evaluation_results.json.
Contains ZERO scenario-specific branching.
"""

import os
import sys
import json
import logging
from pathlib import Path

SIMULATOR_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SIMULATOR_DIR.parent))

from simulator.core.runner import UniversalScenarioRunner, ScenarioContract
from simulator.evaluation.evaluator import UniversalScenarioEvaluator

MANIFEST_PATH = SIMULATOR_DIR / "manifest.json"
RESULTS_DIR = SIMULATOR_DIR / "results"

logging.basicConfig(level=logging.INFO)

def run_all_scenarios():
    print("=" * 115)
    print("   UNIVERSAL DARK PATTERN FRAMEWORK — BEHAVIORAL PREDICATE EVALUATOR")
    print("=" * 115)

    if not MANIFEST_PATH.exists():
        print(f"[ERROR] Manifest file not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    scenarios = manifest.get("scenarios", [])
    runner = UniversalScenarioRunner()
    scenario_pairs = []

    for sc_data in scenarios:
        scenario = ScenarioContract(
            id=sc_data["id"],
            name=sc_data["title"],
            source=sc_data.get("github_repo", ""),
            start_command="python simulator/run_scenarios.py",
            url=sc_data["variant_urls"]["dark"],
            dark_variant=sc_data["variant_urls"]["dark"],
            clean_variant=sc_data["variant_urls"]["clean"],
            ground_truth=sc_data
        )

        dark_res = runner.run_scenario_variant(scenario, variant="dark")
        clean_res = runner.run_scenario_variant(scenario, variant="clean")

        scenario_pairs.append({
            "scenario_id": sc_data["id"],
            "scenario_name": sc_data["title"],
            "dark": dark_res,
            "clean": clean_res
        })

    # Evaluate Results with Behavioral Predicate Evaluator
    evaluator = UniversalScenarioEvaluator()
    eval_scorecard = evaluator.evaluate_suite(scenario_pairs)

    # Print Formatted Evaluation Breakdown Table
    print(f"\n{'#':<4} | {'Scenario Title':<30} | {'Planted Dark Patterns':<28} | {'DARK Status':<12} | {'CLEAN Status':<12}")
    print("-" * 115)

    for sc_res in eval_scorecard["by_scenario"]:
        planted_str = ", ".join(sc_res["planted_patterns"]) if sc_res["planted_patterns"] else "None (Clean)"
        dark_st = sc_res["dark_variant"]["status"]
        clean_st = sc_res["clean_variant"]["status"]
        print(f"{sc_res['scenario_id']:<4} | {sc_res['scenario_name']:<30} | {planted_str:<28} | {dark_st:<12} | {clean_st:<12}")

    # Print Overall Scorecard Metrics
    overall = eval_scorecard["overall"]
    print("\n" + "=" * 115)
    print("   UNIVERSAL FRAMEWORK AGGREGATE SCORECARD METRICS")
    print("=" * 115)
    print(f"  • True Positives (TP)  : {overall['tp']}")
    print(f"  • False Positives (FP) : {overall['fp']}")
    print(f"  • False Negatives (FN) : {overall['fn']}")
    print(f"  • True Negatives (TN)  : {overall['tn']}")
    print(f"  • Precision            : {overall['precision_pct']}%")
    print(f"  • Recall               : {overall['recall_pct']}%")
    print(f"  • F1-Score             : {overall['f1_score']}")
    print("=" * 115)

    # Print Confusion Matrix By Pattern Category
    print("\n" + "=" * 115)
    print("   CONFUSION MATRIX BY DARK PATTERN CATEGORY")
    print("=" * 115)
    print(f"{'Category':<25} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'TN':<4} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<8}")
    print("-" * 115)
    for cat, p_met in eval_scorecard["by_pattern"].items():
        print(f"{cat:<25} | {p_met['tp']:<4} | {p_met['fp']:<4} | {p_met['fn']:<4} | {p_met['tn']:<4} | {p_met['precision_pct']:<10}% | {p_met['recall_pct']:<10}% | {p_met['f1_score']:<8}")
    print("=" * 115 + "\n")

    # Save Machine-Readable Evaluation Results JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_scorecard, f, indent=2)

    print(f"[OK] Machine-readable results saved to {RESULTS_DIR / 'evaluation_results.json'}\n")

if __name__ == "__main__":
    run_all_scenarios()
