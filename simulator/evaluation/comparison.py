"""
Differential Behavior Comparator Module
Calculates behavioral and structural deltas between Clean and Dark variant observations.
Identifies changes in checkbox pre-selections, prices, countdown timers, shaming text,
visual asymmetry, and cancellation barriers.
"""

import re
from typing import Dict, Any, List

class DifferentialComparator:
    def compare_behavior(
        self,
        clean_result: Dict[str, Any],
        dark_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares observed evidence differences between CLEAN and DARK variants of a scenario.
        Identifies structural, visual, text, pricing, selection, and behavioral deltas.
        """
        clean_obs = clean_result.get("observation", {})
        dark_obs = dark_result.get("observation", {})

        clean_elements = clean_obs.get("elements", [])
        dark_elements = dark_obs.get("elements", [])

        clean_texts = [t.lower() for t in clean_obs.get("texts", [])]
        dark_texts = [t.lower() for t in dark_obs.get("texts", [])]

        diff = {
            "checkbox_preselection_diff": False,
            "prechecked_items_in_dark": [],
            "price_jump_diff": False,
            "price_delta": 0.0,
            "late_unrequested_fee_in_dark": False,
            "timer_urgency_diff": False,
            "timer_text_in_dark": [],
            "shaming_opt_out_diff": False,
            "shaming_text_in_dark": [],
            "visual_asymmetry_diff": False,
            "asymmetry_details": [],
            "cancellation_barrier_diff": False,
            "cancellation_details": [],
            "misdirection_diff": False,
            "misdirection_details": [],
            "clean_variant_is_clean": True,
            "raw_text_delta": []
        }

        # 1. Checkbox Pre-selection Delta (pre_selected_options)
        dark_prechecked = [e for e in dark_obs.get("checkboxes", []) if e.get("checked") is True]
        clean_prechecked = [e for e in clean_obs.get("checkboxes", []) if e.get("checked") is True]

        if len(dark_prechecked) > len(clean_prechecked):
            diff["checkbox_preselection_diff"] = True
            diff["prechecked_items_in_dark"] = [e.get("text") or e.get("id") for e in dark_prechecked]

        # Check if Clean variant has zero pre-checked checkboxes
        if len(clean_prechecked) > 0:
            diff["clean_variant_is_clean"] = False

        # 2. Countdown Timer & Urgency Pressure Delta (scarcity_urgency)
        dark_timers = dark_obs.get("timers", [])
        has_dark_timer = len(dark_timers) > 0 or any("hurry" in t or "ends in" in t or "only" in t and "left" in t for t in dark_texts)
        has_clean_timer = any("hurry" in t or "ends in" in t for t in clean_texts)

        if has_dark_timer and not has_clean_timer:
            diff["timer_urgency_diff"] = True
            diff["timer_text_in_dark"] = [t for t in dark_texts if "hurry" in t or "ends in" in t or "only" in t and "left" in t]

        # 3. Hidden Fees & Price Jump Delta (hidden_delayed_costs)
        dark_prices = [p["amount"] for p in dark_obs.get("prices", [])]
        clean_prices = [p["amount"] for p in clean_obs.get("prices", [])]

        dark_has_fee_note = any("mandatory" in t or "service & processing fee" in t or "resort" in t or "platform service fee" in t for t in dark_texts)
        clean_has_fee_note = any("mandatory" in t or "service & processing fee" in t for t in clean_texts)

        if dark_has_fee_note and not clean_has_fee_note:
            diff["late_unrequested_fee_in_dark"] = True
            diff["price_jump_diff"] = True

        if dark_prices and clean_prices:
            max_dark_price = max(dark_prices)
            max_clean_price = max(clean_prices)
            if max_dark_price > max_clean_price:
                diff["price_jump_diff"] = True
                diff["price_delta"] = round(max_dark_price - max_clean_price, 2)

        # 4. Confirmshaming & Guilt-Inducing Opt-Out Text Delta (confirmshaming)
        shaming_keywords = ["hate saving money", "prefer paying full price", "prefer overpaying", "missing out on savings", "prefer paying more"]
        dark_shaming = [t for t in dark_texts if any(sk in t for sk in shaming_keywords)]
        clean_shaming = [t for t in clean_texts if any(sk in t for sk in shaming_keywords)]

        if dark_shaming and not clean_shaming:
            diff["shaming_opt_out_diff"] = True
            diff["shaming_text_in_dark"] = dark_shaming

        # 5. Visual Asymmetry Delta (visual_asymmetry)
        dark_links = dark_obs.get("links", [])
        dark_has_deemphasized_decline = any(
            l.get("contrastRatio", 4.5) < 2.0 or l.get("fontSize", 14) < 11
            for l in dark_links
            if "decline" in l.get("text", "").lower() or "no thanks" in l.get("text", "").lower()
        )
        clean_has_deemphasized_decline = any(
            l.get("contrastRatio", 4.5) < 2.0
            for l in clean_obs.get("links", [])
            if "decline" in l.get("text", "").lower() or "reject" in l.get("text", "").lower()
        )

        if dark_has_deemphasized_decline and not clean_has_deemphasized_decline:
            diff["visual_asymmetry_diff"] = True
            diff["asymmetry_details"].append("Low contrast / tiny font size on decline option in DARK variant")

        # 6. Cancellation Barrier & Forced Continuity Delta (forced_continuity)
        dark_fc = any(
            "auto-renew" in t or "registered mail" in t or "telephone" in t or "step 1 of 4" in t or "lose access to" in t or "annual billing" in t and "selected by default" in t
            for t in dark_texts
        )
        clean_fc = any("registered mail" in t or "step 1 of 4" in t for t in clean_texts)

        if dark_fc and not clean_fc:
            diff["cancellation_barrier_diff"] = True
            diff["cancellation_details"].append("Multi-step cancellation barrier or auto-renewal fine-print present in DARK variant")

        # 7. Misdirection & Deceptive Link Delta (misdirection)
        dark_misdirect = any(
            "download now (fast setup)" in t or "sponsored browser toolbar" in t or "price adjusted" in t or "price increased" in t
            for t in dark_texts
        )
        clean_misdirect = any("sponsored browser toolbar" in t for t in clean_texts)

        if dark_misdirect and not clean_misdirect:
            diff["misdirection_diff"] = True
            diff["misdirection_details"].append("Primary CTA leads to partner toolbar or bait-and-switch price jump in DARK variant")

        # Raw Text Delta
        clean_text_set = set(clean_texts)
        dark_unique_texts = [t for t in dark_texts if t not in clean_text_set]
        diff["raw_text_delta"] = dark_unique_texts[:10]

        return diff
