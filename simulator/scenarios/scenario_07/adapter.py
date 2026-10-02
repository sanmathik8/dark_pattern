"""
Scenario 07 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 7
        self.title = "Travel Booking Engine"
        self.github_repo = "https://github.com/vuejs/vue.git"
        self.commit_hash = "8cf5522e8910b8bb0982367c3b28b7134371900a"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
