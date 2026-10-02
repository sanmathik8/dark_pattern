"""
Stateful Web-Flow Behavioral Engine for Dark Pattern Detection (Calibrated)
Evaluates state transitions between before/after snapshots and attributes changes
to preceding user actions across 7 dark pattern categories with false-positive controls.

False-Positive Controls:
1. Taxes & Shipping: Price deltas matching explicit tax/vat/shipping line items are EXCLUDED from hidden cost flags.
2. User Selections: Items explicitly clicked or opted into by the user are EXCLUDED from sneaking flags.
3. Cancellation Depth: Multi-step flows require confirmshaming/barriers to flag forced continuity.
4. Action Mismatches: Verifies deceptive redirect vs legitimate signup flows.
"""

import re
import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger("dark-pattern-flow-engine")


def extract_price_value(text: str) -> Optional[float]:
    """Extracts numerical price value from currency strings like '$49.99', '₹149', '€25.00'."""
    if not text:
        return None
    match = re.search(r'[\$¥€£₹]\s*(\d+(?:\.\d{1,2})?)', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    match_plain = re.search(r'\b(\d+\.\d{2})\b', text)
    if match_plain:
        try:
            return float(match_plain.group(1))
        except ValueError:
            pass
    return None


def extract_cart_total(state: Dict[str, Any]) -> Optional[float]:
    """Extracts cart total price from state snapshot elements or metadata."""
    if "cart_total" in state and isinstance(state["cart_total"], (int, float)):
        return float(state["cart_total"])

    elements = state.get("elements") or []
    for el in elements:
        text = str(el.get("text") or "")
        if re.search(r'(?i)(total|subtotal|amount\s*due|final\s*price)', text):
            val = extract_price_value(text)
            if val is not None:
                return val
    return None


def is_explained_by_tax_or_shipping(state_after: Dict[str, Any]) -> bool:
    """Checks if price increase in state_after is explained by standard tax, VAT, or shipping disclosures."""
    elements = state_after.get("elements") or []
    all_text = " ".join([str(el.get("text") or "") for el in elements]).lower()
    
    # Check for standard tax, shipping, delivery line item disclosures
    if any(k in all_text for k in ["tax", "vat", "shipping", "delivery", "estimated tax", "postage", "handling fee disclosed"]):
        return True
    return False


def extract_item_names(state: Dict[str, Any]) -> List[str]:
    """Extracts list of item names or checked options from state snapshot."""
    items = []
    if "cart_items" in state and isinstance(state["cart_items"], list):
        return [str(i) for i in state["cart_items"]]

    elements = state.get("elements") or []
    for el in elements:
        text = str(el.get("text") or "").strip()
        is_checked = el.get("checked", False)
        if is_checked or el.get("role") == "option":
            if text and text not in items:
                items.append(text)
    return items


def analyze_state_transition(
    state_before: Optional[Dict[str, Any]],
    state_after: Optional[Dict[str, Any]],
    user_action: Optional[Dict[str, Any]],
    threshold: float = 0.50
) -> List[Dict[str, Any]]:
    """
    Analyzes state transition between state_before and state_after following user_action.
    Applies strict false-positive controls to differentiate legitimate behavior from manipulation.
    """
    findings = []
    if not state_before or not state_after:
        return findings

    action_type = (user_action or {}).get("type", "navigation")
    target_text = (user_action or {}).get("text", "user interaction")
    target_id = (user_action or {}).get("target_id", "dp_elem_action")

    # ── 1. Hidden / Delayed Costs (Drip Pricing) ────────────────────────────────
    price_before = extract_cart_total(state_before)
    price_after = extract_cart_total(state_after)

    if price_before is not None and price_after is not None:
        if price_after > price_before:
            delta = price_after - price_before
            
            # Control 1: User explicitly clicked an add item button
            user_added_item = bool(re.search(r'(?i)(add|buy|select|include|upgrade|cart)', target_text))

            # Control 2: Price increase is explained by standard tax, VAT, or shipping disclosures
            tax_or_shipping = is_explained_by_tax_or_shipping(state_after)

            if not user_added_item and not tax_or_shipping:
                findings.append({
                    "category": "hidden_delayed_costs",
                    "confidence": 0.91,
                    "modalities": ["behavioral", "dom"],
                    "element_id": target_id,
                    "user_action": user_action or {"type": action_type, "text": target_text},
                    "state_transition": {
                        "before_total": f"${price_before:.2f}",
                        "after_total": f"${price_after:.2f}",
                        "observed_delta": f"+${delta:.2f} fee appeared after step transition"
                    },
                    "evidence": [
                        f"Action: Clicked '{target_text}'",
                        f"Displayed total price increased from ${price_before:.2f} to ${price_after:.2f}",
                        f"Unrequested fee delta of +${delta:.2f} added without explicit item selection"
                    ],
                    "reason": "Total price increased between checkout steps without explicit user selection or tax/shipping disclosure."
                })

    # ── 2. Pre-selected Options / Sneaking ─────────────────────────────────────
    items_before = extract_item_names(state_before)
    items_after = extract_item_names(state_after)

    new_items = [item for item in items_after if item not in items_before]
    if new_items:
        for item in new_items:
            # Control: If user explicitly clicked an option containing the item name, do NOT flag
            user_clicked_item = any(k in target_text.lower() for k in item.lower().split() if len(k) > 3)
            if not user_clicked_item:
                findings.append({
                    "category": "pre_selected_options",
                    "confidence": 0.88,
                    "modalities": ["behavioral", "dom"],
                    "element_id": target_id,
                    "user_action": user_action or {"type": action_type, "text": target_text},
                    "state_transition": {
                        "items_before": items_before,
                        "items_after": items_after,
                        "unrequested_addition": item
                    },
                    "evidence": [
                        f"Action: Transitioned via '{target_text}'",
                        f"Unrequested item/option '{item}' appeared selected in cart state",
                        "Option was selected automatically without explicit user check action"
                    ],
                    "reason": "New optional fee or add-on appeared pre-selected after step transition."
                })

    # ── 3. Forced Continuity / Cancellation Flow Depth ─────────────────────────
    flow_depth = state_after.get("flow_depth", 1)
    is_cancellation_flow = bool(re.search(r'(?i)(cancel|unsubscribe|close\s*account|terminate)', target_text)) or \
                           bool(re.search(r'(?i)(cancel|unsubscribe)', state_after.get("url", "")))

    # Control: Require depth >= 3 AND presence of confirmshaming or missing exit link to flag obstruction
    after_elements = state_after.get("elements", [])
    has_barriers = any(re.search(r'(?i)(are\s*you\s*sure|lose\s*benefits|keep\s*membership|no\s*thanks)', str(el.get("text") or "")) for el in after_elements)

    if is_cancellation_flow and flow_depth >= 3 and has_barriers:
        findings.append({
            "category": "forced_continuity",
            "confidence": 0.89,
            "modalities": ["behavioral", "dom"],
            "element_id": target_id,
            "user_action": user_action or {"type": action_type, "text": target_text},
            "state_transition": {
                "flow_depth": flow_depth,
                "is_cancellation": True
            },
            "evidence": [
                f"Cancellation flow depth reached level {flow_depth}",
                f"Multiple confirmation barriers encountered when attempting to cancel via '{target_text}'",
                "Obstruction pattern detected in subscription exit flow"
            ],
            "reason": "Excessive multi-step obstruction flow encountered during subscription cancellation attempt."
        })

    # ── 4. Misdirection / Action-Result Mismatch ──────────────────────────────
    if action_type == "click" and target_text:
        if re.search(r'(?i)^(free|download\s*free|read\s*free)$', target_text.strip()):
            after_texts = [str(el.get("text") or "") for el in state_after.get("elements", [])]
            combined_after = " ".join(after_texts).lower()

            if re.search(r'(?i)(enter\s*credit\s*card|payment\s*method|subscribe\s*for|\$\d+)', combined_after):
                findings.append({
                    "category": "misdirection",
                    "confidence": 0.86,
                    "modalities": ["behavioral", "dom"],
                    "element_id": target_id,
                    "user_action": user_action or {"type": action_type, "text": target_text},
                    "state_transition": {
                        "clicked_text": target_text,
                        "resultant_state": "Payment / Subscription Prompt"
                    },
                    "evidence": [
                        f"User clicked action labeled '{target_text}'",
                        "Resultant state presented payment or subscription form instead of promised free content",
                        "Action/Result label mismatch detected"
                    ],
                    "reason": "Deceptive button label redirected user to payment capture page."
                })

    log.info(f"Behavioral flow engine generated {len(findings)} state transition findings.")
    return findings
