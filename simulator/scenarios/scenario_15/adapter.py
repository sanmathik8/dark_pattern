"""
Scenario 15 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 15
        self.title = "Search Engine & Native Ad Trap"
        self.github_repo = "https://github.com/angular/angular.git"
        self.commit_hash = "e12a4b8905391d1e6702c2f109289871bb219802"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
