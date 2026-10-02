"""
Scenario 01 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 1
        self.title = "Flash-Sale Store"
        self.github_repo = "https://github.com/gothinkster/realworld.git"
        self.commit_hash = "a5d89f13e734c3111f181640a33116bcbf29d2bf"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
