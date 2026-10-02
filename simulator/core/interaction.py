"""
Universal Interaction Module
Provides generic, non-scenario-specific browser interaction primitives.
"""

from typing import Any, Optional
import logging

log = logging.getLogger("simulator-interaction")

class UniversalInteraction:
    def __init__(self, page_object: Any = None):
        self.page = page_object

    def click(self, selector: str) -> bool:
        """Clicks target selector."""
        if self.page:
            try:
                self.page.click(selector, timeout=3000)
                return True
            except Exception as e:
                log.debug(f"Click failed on {selector}: {e}")
                return False
        return False

    def fill(self, selector: str, value: str) -> bool:
        """Fills input element with value."""
        if self.page:
            try:
                self.page.fill(selector, value, timeout=3000)
                return True
            except Exception as e:
                log.debug(f"Fill failed on {selector}: {e}")
                return False
        return False

    def submit(self, selector: str) -> bool:
        """Submits form target."""
        if self.page:
            try:
                self.page.press(selector, "Enter", timeout=3000)
                return True
            except Exception:
                return False
        return False

    def wait(self, duration_ms: int = 1000):
        """Waits for specified milliseconds."""
        if self.page:
            try:
                self.page.wait_for_timeout(duration_ms)
            except Exception:
                pass
