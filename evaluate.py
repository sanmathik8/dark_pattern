"""
Comprehensive Stateful & Behavioral Evaluation Suite for Dark Pattern Detection
Evaluates system across multi-step flow scenarios and static benchmark domains:
1. Cart Drip Price Increases ($49 -> $61 after step transition)
2. Unrequested Item Additions (auto-added warranty)
3. Multi-step Cancellation Barriers (depth level 3 + confirmshaming barrier)
4. Misdirection Action/Result Mismatches (clicked Free E-Book -> payment form)
5. Legitimate Price & Tax Additions (False Positive Control)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from backend.app import model_bundle, load_models, detect, DetectRequest
from backend.text_branch import CATEGORIES

BASE_DIR = Path(__file__).parent
SAMPLES_PATH = BASE_DIR / "test_samples" / "sample_data.json"

logging.basicConfig(level=logging.ERROR)


def run_stateful_behavioral_evaluation():
    print("=" * 75)
    print("   STATEFUL WEB-FLOW DARK PATTERN DETECTOR — EVALUATION SUITE")
    print("=" * 75)

    load_models()
    model_type = model_bundle.get("type", "heuristic_fallback")
    print(f"Loaded ML & Flow Engine: {model_type}\n")

    # ── 1. Stateful Behavioral Flow Scenarios ──────────────────────────────────
    print("-- 1. Behavioral State Transition Scenarios --")
    print(f"{'Scenario Name':<35} | {'Expected Pattern':<22} | {'Result':<10} | {'Observed Evidence'}")
    print("-" * 105)

    scenarios = [
        {
            "name": "Cart Drip Pricing (+$12 fee)",
            "expected_category": "hidden_delayed_costs",
            "state_before": {"cart_total": 49.00, "elements": [{"text": "Total: $49.00"}]},
            "state_after": {"cart_total": 61.00, "elements": [{"text": "Total: $61.00"}]},
            "user_action": {"type": "click", "text": "Continue to Shipping"},
            "is_legitimate": False
        },
        {
            "name": "Unrequested Item Addition",
            "expected_category": "pre_selected_options",
            "state_before": {"cart_items": ["Laptop"], "elements": []},
            "state_after": {"cart_items": ["Laptop", "2-Year Warranty ($19.99)"], "elements": [{"checked": True, "text": "2-Year Warranty"}]},
            "user_action": {"type": "click", "text": "Proceed to Payment"},
            "is_legitimate": False
        },
        {
            "name": "Cancellation Obstruction (Depth 3)",
            "expected_category": "forced_continuity",
            "state_before": {"flow_depth": 2, "url": "https://site.com/account/cancel"},
            "state_after": {
                "flow_depth": 3,
                "url": "https://site.com/account/cancel/confirm",
                "elements": [{"text": "Are you sure? You will lose all membership benefits!"}]
            },
            "user_action": {"type": "click", "text": "I still want to cancel my subscription"},
            "is_legitimate": False
        },
        {
            "name": "Action-Result Misdirection",
            "expected_category": "misdirection",
            "state_before": {"elements": [{"text": "Download Free PDF"}]},
            "state_after": {
                "elements": [{"text": "Enter credit card details to subscribe for $14.99/mo"}]
            },
            "user_action": {"type": "click", "text": "Download Free PDF"},
            "is_legitimate": False
        },
        {
            "name": "Legitimate Tax & Shipping Add (Control)",
            "expected_category": None,
            "state_before": {"cart_total": 50.00, "elements": [{"text": "Subtotal: $50.00"}]},
            "state_after": {"cart_total": 54.50, "elements": [{"text": "Subtotal: $50.00"}, {"text": "Estimated Tax & Shipping: $4.50"}]},
            "user_action": {"type": "click", "text": "Continue to Payment"},
            "is_legitimate": True
        }
    ]

    for sc in scenarios:
        req = DetectRequest(
            state_before=sc["state_before"],
            state_after=sc["state_after"],
            user_action=sc["user_action"],
            threshold=0.50
        )
        res = detect(req)
        findings = res.findings

        found_cat = findings[0].category if findings else None
        ev_str = findings[0].evidence[0] if findings and findings[0].evidence else "Clean / Legitimate"

        passed = (found_cat == sc["expected_category"]) if not sc["is_legitimate"] else (len(findings) == 0)
        status_str = "PASS" if passed else "FAIL"

        print(f"{sc['name']:<35} | {(sc['expected_category'] or 'None (Clean)'):<22} | [{status_str}]    | {ev_str[:35]}...")

    # ── 2. Static Benchmark Evaluation ────────────────────────────────────────
    print("\n-- 2. Threshold Performance Benchmark --")
    print(f"{'Threshold':<12} | {'Total Findings':<15} | {'Clean Page False Positives':<26}")
    print("-" * 65)

    if SAMPLES_PATH.exists():
        with open(SAMPLES_PATH, "r") as f:
            domains_data = json.load(f)

        for th in [0.50, 0.60, 0.70, 0.80, 0.90]:
            total_found = 0
            clean_found = 0
            for domain_name, data in domains_data.items():
                req = DetectRequest(
                    elements=data.get("elements", []),
                    texts=data.get("texts", []),
                    url=data.get("url", ""),
                    threshold=th
                )
                res = detect(req)
                count = res.dark_patterns_count
                total_found += count
                if "clean" in domain_name:
                    clean_found += count
            print(f"  {th:.2f}        | {total_found:<15} | {clean_found:<26}")

    print("\n[OK] Stateful & Behavioral evaluation completed successfully.\n")


if __name__ == "__main__":
    run_stateful_behavioral_evaluation()
