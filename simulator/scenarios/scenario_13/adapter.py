"""
Scenario 13 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 13
        self.title = "Social Media Privacy Settings"
        self.github_repo = "https://github.com/twbs/bootstrap.git"
        self.commit_hash = "c47bf1b2a95c479e0f6e1088a2ef8673f82161f3"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
