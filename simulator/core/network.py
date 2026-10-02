"""
Universal Network Observer Module
Monitors HTTP requests and API activities.
"""

from typing import List, Dict, Any

class UniversalNetworkObserver:
    def __init__(self):
        self.requests: List[Dict[str, Any]] = []

    def start_tracing(self, page_object: Any):
        """Attaches network request listener to page."""
        if page_object:
            try:
                page_object.on("request", lambda req: self.requests.append({
                    "url": req.url,
                    "method": req.method,
                    "headers": dict(req.headers)
                }))
            except Exception:
                pass

    def get_captured_requests() -> List[Dict[str, Any]]:
        return self.requests
