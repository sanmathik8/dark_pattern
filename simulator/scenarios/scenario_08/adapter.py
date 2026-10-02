"""
Scenario 08 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 8
        self.title = "Food Delivery App"
        self.github_repo = "https://github.com/tailwindlabs/tailwindcss.git"
        self.commit_hash = "e12a4b8905391d1e6702c2f109289871bb219802"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
