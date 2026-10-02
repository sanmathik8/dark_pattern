"""
Scenario 09 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 9
        self.title = "SaaS Pricing & Billing"
        self.github_repo = "https://github.com/vercel/next.js.git"
        self.commit_hash = "fa1298c47b590e0b3c61b12987349b10925c1920"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
