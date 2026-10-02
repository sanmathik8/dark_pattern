"""
Scenario 12 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 12
        self.title = "Product Page (Bait & Switch)"
        self.github_repo = "https://github.com/facebook/react.git"
        self.commit_hash = "b26d8338e55c68f128d8b9d8858f9188e7b99a12"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
