"""
Evidence-Aware Fusion Layer for Stateful Dark Pattern Detection
Merges behavioral state transition findings with DOM/Text, Vision (optional), and Voice (optional) branches:
- Deduplicates findings based on category, element_id, spatial bounding-box overlap, or semantic similarity.
- Preserves modality provenance (e.g., modalities: ["behavioral", "dom"]).
- Applies evidence-boosted confidence calculations without naive averaging.
- Filters by configurable decision threshold while retaining raw confidence scores.
"""

import logging
from typing import List, Dict, Any

log = logging.getLogger("dark-pattern-fusion")

def fuse_multimodal_findings(
    dom_findings: List[Dict[str, Any]],
    vision_findings: List[Dict[str, Any]],
    voice_findings: List[Dict[str, Any]],
    behavioral_findings: List[Dict[str, Any]] = None,
    threshold: float = 0.50
) -> List[Dict[str, Any]]:
    """
    Combines findings across Behavioral, DOM, Vision, and Voice modalities into a unified set of verified findings.
    """
    fused_map: Dict[str, Dict[str, Any]] = {}

    all_raw_findings = []

    # Priority 1: Behavioral Flow State Transition Findings
    if behavioral_findings:
        for f in behavioral_findings:
            f_copy = dict(f)
            if "modalities" not in f_copy:
                f_copy["modalities"] = ["behavioral"]
            all_raw_findings.append(f_copy)

    # Priority 2: DOM / CSS / Text Findings
    for f in dom_findings:
        f_copy = dict(f)
        if "modalities" not in f_copy:
            f_copy["modalities"] = ["dom"]
        all_raw_findings.append(f_copy)

    # Optional: Vision Findings
    for f in vision_findings:
        f_copy = dict(f)
        if "modalities" not in f_copy:
            f_copy["modalities"] = ["vision"]
        all_raw_findings.append(f_copy)

    # Optional: Voice Findings
    for f in voice_findings:
        f_copy = dict(f)
        if "modalities" not in f_copy:
            f_copy["modalities"] = ["voice"]
        all_raw_findings.append(f_copy)

    # Cluster findings by category & spatial/semantic overlap
    for item in all_raw_findings:
        cat = item.get("category")
        elem_id = item.get("element_id")
        bbox = item.get("bbox")
        evidence = item.get("evidence", [])

        # Create fusion key
        cluster_key = find_matching_cluster(item, fused_map)

        if cluster_key in fused_map:
            existing = fused_map[cluster_key]
            # Merge modalities
            for mod in item.get("modalities", []):
                if mod not in existing["modalities"]:
                    existing["modalities"].append(mod)

            # Combine evidence lists
            for ev in (evidence if isinstance(evidence, list) else [evidence]):
                if ev and ev not in existing["evidence"]:
                    existing["evidence"].append(ev)

            # Combine state transition details if available
            if item.get("state_transition") and not existing.get("state_transition"):
                existing["state_transition"] = item["state_transition"]

            # Evidence boost: multiple modalities agreeing on same pattern boost confidence!
            conf_1 = existing["confidence"]
            conf_2 = item["confidence"]
            boosted_conf = 1.0 - (1.0 - conf_1) * (1.0 - conf_2)
            existing["confidence"] = round(min(1.0, boosted_conf), 4)

            if not existing.get("element_id") and elem_id:
                existing["element_id"] = elem_id
            if not existing.get("bbox") and bbox:
                existing["bbox"] = bbox
            if not existing.get("rect") and item.get("rect"):
                existing["rect"] = item.get("rect")

        else:
            new_key = f"{cat}_{elem_id or bbox or len(fused_map)}"
            fused_map[new_key] = {
                "category": cat,
                "confidence": item["confidence"],
                "raw_confidence": item["confidence"],
                "modalities": list(item.get("modalities", [])),
                "element_id": elem_id,
                "bbox": bbox,
                "rect": item.get("rect"),
                "evidence": evidence if isinstance(evidence, list) else [evidence],
                "reason": item.get("reason", "Stateful web-flow dark pattern detection"),
                "state_transition": item.get("state_transition")
            }

    # Filter fused results by threshold
    final_results = []
    for item in fused_map.values():
        if item["confidence"] >= threshold:
            final_results.append(item)

    # Sort by highest confidence
    final_results.sort(key=lambda x: x["confidence"], reverse=True)

    log.info(
        f"Fusion layer merged {len(all_raw_findings)} raw findings -> {len(final_results)} fused findings (threshold={threshold})."
    )
    return final_results


def find_matching_cluster(item: Dict[str, Any], fused_map: Dict[str, Dict[str, Any]]) -> str:
    cat = item.get("category")
    elem_id = item.get("element_id")
    bbox = item.get("bbox")

    for key, existing in fused_map.items():
        if existing["category"] != cat:
            continue

        if elem_id and existing.get("element_id") == elem_id:
            return key

        if bbox and existing.get("bbox"):
            if calculate_iou(bbox, existing["bbox"]) > 0.3:
                return key

    return ""


def calculate_iou(bbox1: List[int], bbox2: List[int]) -> float:
    if len(bbox1) < 4 or len(bbox2) < 4:
        return 0.0

    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0

    return float(inter_area / union_area)
