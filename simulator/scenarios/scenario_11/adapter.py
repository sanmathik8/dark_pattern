"""
Scenario 11 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 11
        self.title = "Software Download Portal"
        self.github_repo = "https://github.com/lodash/lodash.git"
        self.commit_hash = "2f79053d2bc7c40562e8111e13e0c0d0c3ab4ef5"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
