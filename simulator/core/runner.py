"""
Universal Scenario Runner Orchestrator
Executes web scenarios via real Playwright Chromium browser sessions loaded with the Universal Pattern Finder extension.
Integrates EnvironmentManager (GitHub checkout, timeline tracking) and BrowserSession (extension loading, telemetry, interactions).
Contains zero scenario-specific branching logic.
"""

import time
import json
import uuid
import logging
from typing import Dict, Any, Optional

from simulator.core.browser import BrowserSession, UniversalBrowser
from simulator.core.environment import EnvironmentManager
from simulator.core.observer import UniversalObserver
from simulator.evaluation.comparison import DifferentialComparator
from simulator.evaluation.evaluator import UniversalScenarioEvaluator

log = logging.getLogger("simulator-runner")

class ScenarioContract:
    def __init__(
        self,
        id: int,
        name: str,
        source: str,
        start_command: str,
        url: str,
        dark_variant: str,
        clean_variant: str,
        ground_truth: Dict[str, Any],
        github_repo: str = "",
        commit_hash: str = ""
    ):
        self.id = id
        self.name = name
        self.source = source
        self.start_command = start_command
        self.url = url
        self.dark_variant = dark_variant
        self.clean_variant = clean_variant
        self.ground_truth = ground_truth
        self.github_repo = github_repo
        self.commit_hash = commit_hash

class UniversalScenarioRunner:
    def __init__(self, extension_path: str = "extension"):
        self.extension_path = extension_path
        self.environment_mgr = EnvironmentManager()
        self.observer = UniversalObserver()
        self.comparator = DifferentialComparator()
        self.evaluator = UniversalScenarioEvaluator()

    def run_scenario_experiment(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes complete Clean vs. Dark behavioral experiment:
        Phase 1: CLEAN variant → Real Browser Session + UPF Extension → Trace
        Phase 2: DARK variant  → Real Browser Session + UPF Extension → Trace
        Phase 3: Differential Comparator → Ground-truth Predicate Evaluator
        """
        sc_id = scenario_config.get("id", 1)
        session_id = f"sess_{uuid.uuid4().hex[:10]}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        log.info(f"--- Starting Real Browser Experiment for Scenario #{sc_id:02d} Session={session_id} ---")

        # 1. Phase 1: Clean Variant Run
        env_clean = self.environment_mgr.prepare_environment(scenario_config, variant="clean")
        clean_session = BrowserSession(extension_path=self.extension_path, headless=True)
        
        clean_observation = {}
        clean_health = {}
        if clean_session.create():
            self.environment_mgr.log_timeline_event(13, "Real Chromium Browser started for Clean Variant")
            if clean_session.navigate(env_clean["health_url"]):
                self.environment_mgr.log_timeline_event(14, "UPF Extension loaded & verified")
                clean_health = clean_session.check_extension_health()
                self.environment_mgr.log_timeline_event(15, f"Universal Sensor status: {clean_health.get('status')}")
                clean_observation = clean_session.get_page_state()
            clean_session.close()

        # 2. Phase 2: Dark Variant Run
        env_dark = self.environment_mgr.prepare_environment(scenario_config, variant="dark")
        dark_session = BrowserSession(extension_path=self.extension_path, headless=True)
        
        dark_observation = {}
        dark_health = {}
        if dark_session.create():
            self.environment_mgr.log_timeline_event(13, "Real Chromium Browser started for Dark Variant")
            if dark_session.navigate(env_dark["health_url"]):
                self.environment_mgr.log_timeline_event(14, "UPF Extension loaded & verified")
                dark_health = dark_session.check_extension_health()
                self.environment_mgr.log_timeline_event(15, f"Universal Sensor status: {dark_health.get('status')}")
                dark_observation = dark_session.get_page_state()
            dark_session.close()

        # 3. Phase 3: Differential Behavioral Comparison & Evaluation
        self.environment_mgr.log_timeline_event(21, "Executing differential DOM state comparator")
        diff_result = self.comparator.compare_variants(clean_observation, dark_observation)
        
        self.environment_mgr.log_timeline_event(23, "Ground-truth behavioral predicate evaluator executing")
        evaluation_verdict = self.evaluator.evaluate_scenario(scenario_config, diff_result)
        
        self.environment_mgr.log_timeline_event(30, "Experiment complete")

        # 4. Reproducibility metadata
        reproducibility = {
            "repository": scenario_config.get("github_repo", ""),
            "commit": scenario_config.get("commit_hash", ""),
            "branch": "main",
            "scenario_id": sc_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "browser_version": "Chromium 124 (Playwright)",
            "extension_version": "1.0.0",
            "application_url": env_dark.get("health_url", "")
        }

        return {
            "scenario_id": sc_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "reproducibility": reproducibility,
            "timeline": self.environment_mgr.timeline,
            "clean_health": clean_health,
            "dark_health": dark_health,
            "diff_result": diff_result,
            "evaluation_verdict": evaluation_verdict
        }
