"""
Ground Truth Schema Validator Module
Validates scenario ground truth definitions.
"""

from typing import Dict, Any, List

class GroundTruthValidator:
    def validate(self, ground_truth: Dict[str, Any]) -> bool:
        """Validates that ground truth dictionary contains required keys."""
        if not isinstance(ground_truth, dict):
            return False
        if "scenario_id" not in ground_truth:
            return False
        if "planted_patterns" not in ground_truth:
            return False
        return True
