"""
Universal Evidence Collector Module
Constructs machine-readable evidence items.
"""

from typing import List, Dict, Any

class EvidenceCollector:
    def create_evidence_item(
        self,
        category: str,
        confidence: float,
        evidence_str: str,
        reason_str: str,
        modality: str = "dom",
        element_id: str = None,
        rect: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Creates a standardized evidence item dictionary."""
        return {
            "category": category,
            "confidence": round(confidence, 4),
            "modality": modality,
            "element_id": element_id or "dp_elem_generic",
            "evidence": [evidence_str] if isinstance(evidence_str, str) else evidence_str,
            "reason": reason_str,
            "rect": rect or {"x": 100, "y": 100, "width": 200, "height": 30}
        }
