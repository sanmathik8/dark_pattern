"""
Scenario 06 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 6
        self.title = "Cookie Consent Banner"
        self.github_repo = "https://github.com/jakearchibald/idb.git"
        self.commit_hash = "a4f891b29d10e82c50a0f9b33a7e289192468ab0"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
