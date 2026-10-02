"""
Scenario 05 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 5
        self.title = "Multi-Step Cancellation Flow"
        self.github_repo = "https://github.com/expressjs/express.git"
        self.commit_hash = "7b0d2d34a45c388277c0147986708b79d2b2a67e"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
