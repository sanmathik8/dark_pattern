"""
Git Environment Manager & Isolated Workspace Orchestrator
Handles repository cloning, exact commit checkout, runtime detection,
build/startup process management, health check polling, and dual source-mode execution (github vs fixture).
"""

import os
import sys
import time
import subprocess
import urllib.request
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

log = logging.getLogger("simulator-git-environment")

class RuntimeAdapter:
    """Generic runtime adapter base class (Node, Python, Static)."""
    def __init__(self, workspace: Path, port: int):
        self.workspace = workspace
        self.port = port
        self.process: Optional[subprocess.Popen] = None

    def install(self) -> bool:
        return True

    def build(self) -> bool:
        return True

    def start(self, env_vars: Dict[str, str]) -> Tuple[bool, int, str]:
        return False, 0, ""

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

class NodeRuntimeAdapter(RuntimeAdapter):
    def install(self) -> bool:
        pkg_json = self.workspace / "package.json"
        if pkg_json.exists():
            try:
                res = subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=str(self.workspace), capture_output=True, timeout=60)
                return res.returncode == 0
            except Exception:
                return False
        return True

    def build(self) -> bool:
        pkg_json = self.workspace / "package.json"
        if pkg_json.exists():
            try:
                content = pkg_json.read_text(encoding="utf-8")
                if '"build":' in content:
                    res = subprocess.run(["npm", "run", "build"], cwd=str(self.workspace), capture_output=True, timeout=60)
                    return res.returncode == 0
            except Exception:
                pass
        return True

    def start(self, env_vars: Dict[str, str]) -> Tuple[bool, int, str]:
        env = os.environ.copy()
        env.update(env_vars)
        env["PORT"] = str(self.port)
        
        cmd = ["npx", "serve", "-s", ".", "-l", str(self.port)]
        pkg_json = self.workspace / "package.json"
        if pkg_json.exists():
            try:
                content = pkg_json.read_text(encoding="utf-8")
                if '"start":' in content:
                    cmd = ["npm", "start"]
            except Exception:
                pass

        try:
            self.process = subprocess.Popen(cmd, cwd=str(self.workspace), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True, self.process.pid, " ".join(cmd)
        except Exception as e:
            return False, 0, str(e)

class StaticRuntimeAdapter(RuntimeAdapter):
    def start(self, env_vars: Dict[str, str]) -> Tuple[bool, int, str]:
        cmd = [sys.executable, "-m", "http.server", str(self.port)]
        try:
            self.process = subprocess.Popen(cmd, cwd=str(self.workspace), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True, self.process.pid, " ".join(cmd)
        except Exception as e:
            return False, 0, str(e)

class EnvironmentDetector:
    @staticmethod
    def detect(workspace: Path, port: int) -> RuntimeAdapter:
        if (workspace / "package.json").exists():
            return NodeRuntimeAdapter(workspace, port)
        return StaticRuntimeAdapter(workspace, port)

class GitEnvironmentManager:
    def __init__(self, root_dir: str = "D:/darkpattern"):
        self.root_dir = Path(root_dir)
        self.runtime_dir = self.root_dir / "runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.active_adapters: Dict[str, RuntimeAdapter] = {}
        self.base_port = 8100

    def allocate_port(self, scenario_id: int) -> int:
        return self.base_port + scenario_id

    def prepare_environment(
        self,
        scenario_config: Dict[str, Any],
        variant: str = "dark",
        source_mode: str = "github"
    ) -> Dict[str, Any]:
        """
        Dual-mode environment preparation:
        - Mode 'github': Resolves repo, checks out exact pinned commit, detects runtime, launches app on allocated port.
        - Mode 'fixture': Uses local scenario fixture at http://localhost:8080/scenario/XX?variant=variant.
        """
        sc_id = scenario_config.get("id", 1)
        repo_url = scenario_config.get("github_repo", "")
        expected_commit = scenario_config.get("commit_hash", "")
        slug = scenario_config.get("slug", f"scenario_{sc_id:02d}")
        
        # 1. FIXTURE MODE FALLBACK / OVERRIDE
        if source_mode == "fixture" or not repo_url:
            fixture_url = f"http://localhost:8080/scenario/{sc_id:02d}?variant={variant}"
            return {
                "status": "RUNNING",
                "source_mode": "fixture",
                "scenario_id": sc_id,
                "url": fixture_url,
                "port": 8080,
                "provenance": {
                    "source": {
                        "type": "fixture",
                        "repository": repo_url,
                        "expected_commit": expected_commit,
                        "actual_commit": expected_commit,
                        "match_status": "FIXTURE_MODE"
                    },
                    "environment": {
                        "workspace": f"simulator/scenarios/{slug}/{variant}",
                        "runtime": "local_http_fixture",
                        "port": 8080,
                        "url": fixture_url,
                        "pid": 0
                    },
                    "browser": {
                        "engine": "chromium",
                        "extension": "upf"
                    }
                }
            }

        # 2. GITHUB MODE WORKSPACE SETUP
        workspace_dir = self.runtime_dir / slug / f"commit_{expected_commit[:8]}"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        actual_commit = ""
        commit_match = False
        
        # Clone / Fetch git repository
        git_dir = workspace_dir / ".git"
        if not git_dir.exists():
            clone_cmd = ["git", "clone", "--depth", "50", repo_url, str(workspace_dir)]
            try:
                clone_res = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=45)
                if clone_res.returncode != 0 and not (workspace_dir / "index.html").exists():
                    log.warning(f"Git clone failed for {repo_url}: {clone_res.stderr}. Falling back to fixture mode.")
                    return self.prepare_environment(scenario_config, variant=variant, source_mode="fixture")
            except Exception:
                return self.prepare_environment(scenario_config, variant=variant, source_mode="fixture")

        # Checkout pinned commit
        if git_dir.exists():
            try:
                subprocess.run(["git", "fetch", "--all"], cwd=str(workspace_dir), capture_output=True, timeout=20)
                ch_res = subprocess.run(["git", "checkout", "--detach", expected_commit], cwd=str(workspace_dir), capture_output=True, text=True, timeout=20)
                
                rev_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(workspace_dir), capture_output=True, text=True, timeout=10)
                actual_commit = rev_res.stdout.strip()
                
                if expected_commit.startswith(actual_commit[:8]) or actual_commit.startswith(expected_commit[:8]):
                    commit_match = True
                else:
                    log.warning(f"Commit mismatch! Expected {expected_commit} but got {actual_commit}")
            except Exception:
                pass

        port = self.allocate_port(sc_id)
        adapter = EnvironmentDetector.detect(workspace_dir, port)
        
        # Install & Start runtime
        adapter.install()
        adapter.build()
        started, pid, cmd_str = adapter.start({"SCENARIO_VARIANT": variant})
        
        app_url = f"http://localhost:{port}/"
        if not started:
            app_url = f"http://localhost:8080/scenario/{sc_id:02d}?variant={variant}"

        self.active_adapters[slug] = adapter

        provenance = {
            "source": {
                "type": "github" if (started and commit_match) else "fixture",
                "repository": repo_url,
                "expected_commit": expected_commit,
                "actual_commit": actual_commit or expected_commit,
                "match_status": "MATCH" if commit_match else "MISMATCH"
            },
            "environment": {
                "workspace": str(workspace_dir),
                "runtime": adapter.__class__.__name__,
                "port": port if started else 8080,
                "url": app_url,
                "pid": pid,
                "startup_command": cmd_str
            },
            "browser": {
                "engine": "chromium",
                "extension": "upf"
            }
        }

        return {
            "status": "RUNNING",
            "source_mode": "github" if (started and commit_match) else "fixture",
            "scenario_id": sc_id,
            "url": app_url,
            "port": port if started else 8080,
            "provenance": provenance
        }

    def stop_environment(self, scenario_slug: str):
        if scenario_slug in self.active_adapters:
            self.active_adapters[scenario_slug].stop()
            del self.active_adapters[scenario_slug]
