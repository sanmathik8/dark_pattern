"""
Text / DOM Branch for Multi-Modal Dark Pattern Detection
Handles multi-label classification and universal DOM heuristic analysis across 7 categories:
1. scarcity_urgency
2. pre_selected_options
3. visual_asymmetry
4. confirmshaming
5. hidden_delayed_costs
6. forced_continuity
7. misdirection
"""

import re
import logging
from typing import List, Dict, Any
import numpy as np

log = logging.getLogger("dark-pattern-text-branch")

CATEGORIES = [
    'scarcity_urgency',
    'pre_selected_options',
    'visual_asymmetry',
    'confirmshaming',
    'hidden_delayed_costs',
    'forced_continuity',
    'misdirection'
]

# Patterns for universal text & DOM heuristics
CONFIRMSHAMING_PATTERNS = [
    r"(?i)no\s*thanks,?\s*i\s*(don't|do\s*not)\s*want",
    r"(?i)no,?\s*i\s*prefer\s*paying\s*full",
    r"(?i)no,?\s*i\s*hate\s*(saving|discounts|free)",
    r"(?i)no\s*thanks,?\s*i'll\s*pay\s*more",
    r"(?i)i'd\s*rather\s*miss\s*out",
]

SCARCITY_URGENCY_PATTERNS = [
    r"(?i)only\s*\d+\s*(left|remaining|in\s*stock)",
    r"(?i)hurry!?",
    r"(?i)limited\s*time\s*(offer|deal)",
    r"(?i)ends\s*in\s*\d+\s*(mins?|minutes?|hours?|secs?|seconds?)",
    r"(?i)\d+\s*people\s*(viewing|bought|in\s*cart)",
    r"(?i)almost\s*sold\s*out",
    r"(?i)last\s*chance",
]

HIDDEN_COST_PATTERNS = [
    r"(?i)(service|handling|resort|processing)\s*fee",
    r"(?i)added\s*(at|during)\s*(checkout|payment)",
    r"(?i)taxes?\s*(and|&)\s*fees?\s*extra",
    r"(?i)additional\s*charge\s*applies",
]

FORCED_CONTINUITY_PATTERNS = [
    r"(?i)auto(matically)?\s*renews?",
    r"(?i)billed\s*(monthly|annually)\s*after\s*trial",
    r"(?i)cancel\s*anytime\s*by\s*calling",
    r"(?i)subscription\s*continues\s*until\s*cancelled",
    r"(?i)free\s*trial.*enter\s*card",
]

PRESELECTED_PATTERNS = [
    r"(?i)pre-?selected",
    r"(?i)added\s*to\s*your\s*cart\s*by\s*default",
    r"(?i)include\s*optional\s*(insurance|protection|warranty)",
]


def analyze_text_and_dom(
    elements: List[Dict[str, Any]],
    model_bundle: Dict[str, Any],
    threshold: float = 0.50
) -> List[Dict[str, Any]]:
    """
    Analyzes DOM element text, attributes, contrast, and pre-selected states.
    Returns structured evidence list for the 7 dark pattern categories.
    """
    findings = []
    if not elements:
        return findings

    # Extract text strings for batch ML classification
    texts = [str(el.get("text") or el.get("ariaLabel") or el.get("placeholder") or "").strip() for el in elements]

    # Batch ML inference
    ml_preds = predict_multilabel_texts(texts, model_bundle)

    for i, el in enumerate(elements):
        elem_id = el.get("id", f"dp_elem_{i}")
        text = texts[i]
        if not text and not el.get("checked"):
            continue

        # Collect heuristic findings for this element
        heuristic_matches = []

        # 1. Pre-selected Options (DOM state check)
        is_checked = el.get("checked", False)
        tag = (el.get("tag") or "").lower()
        role = (el.get("role") or "").lower()
        input_type = (el.get("type") or "").lower()
        is_checkbox = (tag == "input" and input_type in ["checkbox", "radio"]) or role in ["checkbox", "radio"]

        preselect_keywords = ["warranty", "protection", "insurance", "express", "add-on", "addon", "tip", "fee", "tracking", "share", "location", "newsletter", "pre-selected", "preselected", "default", "optional"]

        if is_checked and is_checkbox:
            if any(k in text.lower() for k in preselect_keywords) or any(re.search(p, text) for p in PRESELECTED_PATTERNS):
                heuristic_matches.append({
                    "category": "pre_selected_options",
                    "confidence": 0.88,
                    "evidence": text or "Pre-selected option input",
                    "reason": "Option or add-on item is pre-selected / checked by default."
                })

        for p in PRESELECTED_PATTERNS:
            if re.search(p, text):
                heuristic_matches.append({
                    "category": "pre_selected_options",
                    "confidence": 0.85,
                    "evidence": text,
                    "reason": "Language indicates pre-selected optional charge or subscription."
                })

        # 2. Visual Asymmetry (DOM styling check for deemphasized decline / opt-out elements)
        decline_keywords = ["decline", "reject", "no thanks", "no, thanks", "skip", "opt-out", "don't want", "prefer paying", "prefer overpaying", "cancel subscription"]
        contrast = el.get("contrastRatio")
        font_size = el.get("fontSize", 14)
        if contrast is not None and contrast < 2.5 and (tag in ["button", "a"] or role == "button"):
            if any(dk in text.lower() for dk in decline_keywords):
                heuristic_matches.append({
                    "category": "visual_asymmetry",
                    "confidence": 0.82,
                    "evidence": f"Decline element ('{text}'): Contrast ratio: {contrast}:1, font-size: {font_size}px",
                    "reason": "Decline or opt-out action element has dangerously low contrast or muted visual presence compared to surrounding UI."
                })

        # 3. Confirmshaming
        for p in CONFIRMSHAMING_PATTERNS:
            if re.search(p, text):
                heuristic_matches.append({
                    "category": "confirmshaming",
                    "confidence": 0.90,
                    "evidence": text,
                    "reason": "Emotional guilt / manipulative language used to deter user from declining."
                })

        # 4. Scarcity & Urgency
        for p in SCARCITY_URGENCY_PATTERNS:
            if re.search(p, text):
                heuristic_matches.append({
                    "category": "scarcity_urgency",
                    "confidence": 0.87,
                    "evidence": text,
                    "reason": "Artificial countdown or scarcity constraint detected in element text."
                })

        # 5. Hidden / Delayed Costs
        for p in HIDDEN_COST_PATTERNS:
            if re.search(p, text):
                heuristic_matches.append({
                    "category": "hidden_delayed_costs",
                    "confidence": 0.86,
                    "evidence": text,
                    "reason": "Dormant, delayed, or fine-print fee disclosure detected."
                })

        # 6. Forced Continuity
        for p in FORCED_CONTINUITY_PATTERNS:
            if re.search(p, text):
                heuristic_matches.append({
                    "category": "forced_continuity",
                    "confidence": 0.88,
                    "evidence": text,
                    "reason": "Recurring auto-renewal billing or complex cancellation constraint disclosed."
                })

        # Combine ML prediction with Heuristics
        ml_scores = ml_preds[i] if i < len(ml_preds) else {}

        for cat in CATEGORIES:
            ml_conf = float(ml_scores.get(cat, 0.0))
            h_match = next((h for h in heuristic_matches if h["category"] == cat), None)

            final_conf = ml_conf
            evidence_str = text
            reason_str = "ML text classifier detection"

            if h_match:
                final_conf = max(ml_conf, h_match["confidence"])
                evidence_str = h_match["evidence"]
                reason_str = h_match["reason"]

            min_required_conf = threshold if h_match else max(threshold, 0.65)

            if final_conf >= min_required_conf and final_conf > 0.55:
                findings.append({
                    "category": cat,
                    "confidence": round(final_conf, 4),
                    "modality": "dom",
                    "element_id": elem_id,
                    "evidence": [evidence_str] if isinstance(evidence_str, str) else evidence_str,
                    "reason": reason_str,
                    "rect": el.get("rect")
                })

    return findings


def predict_multilabel_texts(texts: List[str], model_bundle: Dict[str, Any]) -> List[Dict[str, float]]:
    """Runs batch inference using DistilBERT or Linear SVM multi-label model."""
    if not texts:
        return []

    results = []
    model_type = model_bundle.get("type")

    # 1. DistilBERT Multi-label
    if model_type == "transformer" and "model" in model_bundle:
        tokenizer = model_bundle["tokenizer"]
        model = model_bundle["model"]
        device = model_bundle.get("device", "cpu")

        safe_inputs = [t if t.strip() else " " for t in texts]

        inputs = tokenizer(
            safe_inputs, padding=True, truncation=True, max_length=128, return_tensors="pt"
        ).to(device)
        inputs.pop("token_type_ids", None)

        import torch
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits).cpu().numpy()

        for probs_i in probs:
            row_dict = {}
            for idx, cat in enumerate(CATEGORIES):
                # Safe bounds check in case model has different output dimension
                val = float(probs_i[idx]) if idx < len(probs_i) else 0.0
                row_dict[cat] = val
            results.append(row_dict)

    # 2. Linear SVM Multi-label Fallback
    elif model_type == "linear_svm" and "classifier" in model_bundle:
        vectorizer = model_bundle["vectorizer"]
        classifier = model_bundle["classifier"]

        X = vectorizer.transform(texts)
        if hasattr(classifier, "decision_function"):
            decisions = classifier.decision_function(X)
            # Calibrate SVM sigmoid: positive decision values (>0) indicate dark pattern signal; decision <=0 represents neutral text (prob = 0.0)
            probs = np.where(decisions > 0, 1.0 / (1.0 + np.exp(-decisions)), 0.0)
        else:
            probs = classifier.predict(X)

        if probs.ndim == 1:
            probs = np.expand_dims(probs, axis=1)

        for probs_i in probs:
            row_dict = {}
            for idx, cat in enumerate(CATEGORIES):
                val = float(probs_i[idx]) if idx < probs_i.shape[0] else 0.0
                row_dict[cat] = val
            results.append(row_dict)

    else:
        for _ in texts:
            results.append({cat: 0.0 for cat in CATEGORIES})

    return results
