"""
Universal Storage Observer Module
Inspects client-side localStorage and sessionStorage state.
"""

from typing import Dict, Any, Optional

class UniversalStorageObserver:
    def observe_storage(self, page_object: Any) -> Dict[str, Any]:
        """Extracts localStorage and sessionStorage state dictionaries."""
        storage = {"local_storage": {}, "session_storage": {}}
        if page_object:
            try:
                storage["local_storage"] = page_object.evaluate("() => ({...localStorage})") or {}
                storage["session_storage"] = page_object.evaluate("() => ({...sessionStorage})") or {}
            except Exception:
                pass
        return storage
