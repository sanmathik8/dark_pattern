"""
Scenario 04 Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = 4
        self.title = "Streaming Subscription Free Trial"
        self.github_repo = "https://github.com/stripe-samples/checkout-single-subscription.git"
        self.commit_hash = "d1e7c53641f238ab90d3a958b1220a1122ab45e3"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
