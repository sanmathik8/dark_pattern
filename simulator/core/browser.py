"""
Real Browser Session Manager with Dedicated Thread Worker
Manages Playwright Chromium persistent contexts loaded with the local Universal Pattern Finder extension.
All Playwright operations execute on a dedicated single worker thread to ensure Playwright thread safety.
Provides live DOM state inspection, generic browser interaction primitives, and live screenshot stream capture.
"""

import os
import time
import base64
import tempfile
import queue
import threading
import logging
from typing import Optional, Dict, Any, List

log = logging.getLogger("simulator-browser")

class BrowserThreadDispatcher:
    def __init__(self):
        self.cmd_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _worker_loop(self):
        while True:
            func, args, kwargs, result_holder, event = self.cmd_queue.get()
            try:
                res = func(*args, **kwargs)
                result_holder["result"] = res
            except Exception as e:
                result_holder["error"] = e
            finally:
                event.set()
                self.cmd_queue.task_done()

    def execute(self, func, *args, **kwargs):
        event = threading.Event()
        result_holder = {}
        self.cmd_queue.put((func, args, kwargs, result_holder, event))
        event.wait(timeout=15)
        if "error" in result_holder:
            raise result_holder["error"]
        return result_holder.get("result")

GLOBAL_DISPATCHER = BrowserThreadDispatcher()

class BrowserSession:
    def __init__(self, extension_path: str = "extension", headless: bool = False):
        self.extension_path = os.path.abspath(extension_path)
        self.headless = headless
        self.playwright = None
        self.context = None
        self.page = None
        self.user_data_dir = None
        self.active_url = ""
        self.console_events: List[Dict[str, Any]] = []
        self.network_events: List[Dict[str, Any]] = []
        self.last_screenshot_base64: str = ""
        self.last_screenshot_bytes: bytes = b""

    def create(self) -> bool:
        return GLOBAL_DISPATCHER.execute(self._create_impl)

    def _create_impl(self) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.user_data_dir = tempfile.mkdtemp(prefix="upf_profile_")
            
            args = [
                f"--disable-extensions-except={self.extension_path}",
                f"--load-extension={self.extension_path}",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
            
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                args=args,
                viewport={"width": 1280, "height": 800}
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            self.page.on("console", lambda msg: self.console_events.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": time.strftime("%H:%M:%S")
            }))
            self.page.on("request", lambda req: self.network_events.append({
                "method": req.method,
                "url": req.url,
                "timestamp": time.strftime("%H:%M:%S")
            }))
            
            log.info(f"Playwright persistent browser session started with UPF extension at {self.extension_path}")
            return True
        except Exception as e:
            log.warning(f"BrowserSession launch failed: {e}")
            return False

    def navigate(self, url: str) -> bool:
        return GLOBAL_DISPATCHER.execute(self._navigate_impl, url)

    def _navigate_impl(self, url: str) -> bool:
        if not self.page:
            return False
        try:
            self.active_url = url
            self.page.goto(url, wait_until="domcontentloaded", timeout=12000)
            time.sleep(0.5)
            self._capture_screenshot_impl()
            return True
        except Exception as e:
            log.warning(f"BrowserSession navigation failed for {url}: {e}")
            return False

    def capture_screenshot(self) -> str:
        return GLOBAL_DISPATCHER.execute(self._capture_screenshot_impl)

    def _capture_screenshot_impl(self) -> str:
        if not self.page:
            return ""
        try:
            img_bytes = self.page.screenshot(type="jpeg", quality=80)
            self.last_screenshot_bytes = img_bytes
            self.last_screenshot_base64 = base64.b64encode(img_bytes).decode("utf-8")
            return self.last_screenshot_base64
        except Exception as e:
            log.warning(f"Screenshot capture error: {e}")
            return ""

    def check_extension_health(self) -> Dict[str, Any]:
        return GLOBAL_DISPATCHER.execute(self._check_extension_health_impl)

    def _check_extension_health_impl(self) -> Dict[str, Any]:
        if not self.page:
            return {
                "injected": False,
                "sensor_initialized": False,
                "status": "NOT CONNECTED",
                "events_captured": 0,
                "telemetry": "offline"
            }
        try:
            injected = self.page.evaluate("() => typeof window.DarkPatternDetectorInjected !== 'undefined'")
            if not injected:
                content_js_path = os.path.join(self.extension_path, "content.js")
                if os.path.exists(content_js_path):
                    with open(content_js_path, "r", encoding="utf-8") as f:
                        self.page.evaluate(f.read())
                    injected = self.page.evaluate("() => typeof window.DarkPatternDetectorInjected !== 'undefined'")

            return {
                "injected": bool(injected),
                "sensor_initialized": bool(injected),
                "status": "ACTIVE" if injected else "NOT CONNECTED",
                "events_captured": len(self.console_events),
                "network_events_count": len(self.network_events),
                "telemetry": "online" if injected else "offline"
            }
        except Exception:
            return {
                "injected": False,
                "sensor_initialized": False,
                "status": "NOT CONNECTED",
                "events_captured": 0,
                "telemetry": "offline"
            }

    def get_page_state(self) -> Dict[str, Any]:
        return GLOBAL_DISPATCHER.execute(self._get_page_state_impl)

    def _get_page_state_impl(self) -> Dict[str, Any]:
        if not self.page:
            return {"title": "", "url": "", "elements": [], "texts": []}
        try:
            title = self.page.title()
            url = self.page.url
            elements = self.page.evaluate("""
            () => {
                const results = [];
                const candidates = document.querySelectorAll('button, input, a, label, [role="button"], [role="checkbox"], p, h1, h2, h3, div, span');
                candidates.forEach((el, idx) => {
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return;
                    const rect = el.getBoundingClientRect();
                    const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                    if (!text && el.tagName !== 'INPUT') return;
                    results.push({
                        id: el.id || `dp_elem_${idx}`,
                        tag: el.tagName.toLowerCase(),
                        role: el.getAttribute('role') || '',
                        type: el.getAttribute('type') || '',
                        text: text.substring(0, 300),
                        checked: el.checked || el.getAttribute('aria-checked') === 'true' || el.hasAttribute('checked'),
                        color: style.color,
                        backgroundColor: style.backgroundColor,
                        fontSize: parseFloat(style.fontSize) || 14,
                        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
                    });
                });
                return results;
            }
            """) or []
            texts = [e["text"] for e in elements if e.get("text")]
            return {
                "title": title,
                "url": url,
                "elements": elements,
                "texts": texts
            }
        except Exception as e:
            log.warning(f"get_page_state failed: {e}")
            return {"title": "", "url": self.active_url, "elements": [], "texts": []}

    def interact(self, action_type: str, selector: str = "", text: str = "") -> Dict[str, Any]:
        return GLOBAL_DISPATCHER.execute(self._interact_impl, action_type, selector, text)

    def _interact_impl(self, action_type: str, selector: str = "", text: str = "") -> Dict[str, Any]:
        if not self.page:
            return {"success": False, "error": "Browser session active page not found"}
        try:
            action = action_type.lower()
            if action == "click":
                if selector:
                    self.page.click(selector, timeout=4000)
                else:
                    self.page.mouse.click(640, 400)
            elif action == "type":
                if selector and text:
                    self.page.fill(selector, text, timeout=4000)
                elif text:
                    self.page.keyboard.type(text)
            elif action == "scroll":
                self.page.evaluate("window.scrollBy(0, 350)")
            elif action == "hover":
                if selector:
                    self.page.hover(selector, timeout=4000)
            elif action == "focus" and selector:
                self.page.focus(selector, timeout=4000)
            elif action == "navigate" and text:
                self._navigate_impl(text)
            elif action == "back":
                self.page.go_back()
            elif action == "forward":
                self.page.go_forward()

            time.sleep(0.4)
            self._capture_screenshot_impl()
            return {
                "success": True,
                "action": action,
                "url": self.page.url,
                "extension_health": self._check_extension_health_impl()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self):
        try:
            GLOBAL_DISPATCHER.execute(self._close_impl)
        except Exception:
            pass

    def _close_impl(self):
        try:
            if self.page: self.page.close()
            if self.context: self.context.close()
            if self.playwright: self.playwright.stop()
        except Exception:
            pass

class UniversalBrowser:
    def __init__(self, headless: bool = False):
        self.session = BrowserSession(headless=headless)

    def launch(self) -> bool:
        return self.session.create()

    def navigate(self, url: str) -> bool:
        return self.session.navigate(url)

    def close(self):
        self.session.close()

    @property
    def page(self):
        return self.session.page
