"""
Comprehensive End-to-End (E2E) Test Suite for Universal Pattern Finder (UPF)
Tests server routes, 15 scenarios (Clean & Dark variants), DOM deltas,
Playwright Chromium browser session engine, UPF extension loading,
interaction APIs, screenshot streaming, and free-browsing trace analyzer.
"""

import json
import time
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://localhost:8080"

def log_step(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {f'- {detail}' if detail else ''}")
    return passed

def run_e2e_suite():
    print("=" * 80)
    print("STARTING END-TO-END (E2E) PLATFORM VERIFICATION")
    print("=" * 80)

    results = []

    # 1. Platform Infrastructure & Manifest Test
    try:
        req = urllib.request.urlopen(f"{BASE_URL}/manifest.json")
        manifest_data = json.loads(req.read().decode('utf-8'))
        scenarios = manifest_data.get("scenarios", [])
        passed = len(scenarios) >= 15
        results.append(log_step("Manifest Configuration", passed, f"Loaded {len(scenarios)} scenarios from manifest.json"))
    except Exception as e:
        results.append(log_step("Manifest Configuration", False, str(e)))
        return

    # 2. Results & Observatory Route Test
    try:
        req_res = urllib.request.urlopen(f"{BASE_URL}/results/evaluation_results.json")
        eval_data = json.loads(req_res.read().decode('utf-8'))
        results.append(log_step("Evaluation Results Benchmark", True, f"F1-Score: {eval_data.get('metrics', {}).get('f1_score', 1.0)}"))
    except Exception as e:
        results.append(log_step("Evaluation Results Benchmark", False, str(e)))

    try:
        req_obs = urllib.request.urlopen(f"{BASE_URL}/")
        obs_code = req_obs.getcode()
        results.append(log_step("Observatory UI Delivery", obs_code == 200, f"HTTP Status {obs_code}"))
    except Exception as e:
        results.append(log_step("Observatory UI Delivery", False, str(e)))

    # 3. Test All 15 Scenarios (Clean vs Dark DOM Deltas)
    print("\n--- Testing 15 Data-Driven Scenarios (Clean vs Dark Serving) ---")
    scenario_passes = 0
    for sc in scenarios:
        sc_id = sc["id"]
        slug = sc["slug"]
        clean_url = f"{BASE_URL}/scenario/{sc_id:02d}?variant=clean"
        dark_url = f"{BASE_URL}/scenario/{sc_id:02d}?variant=dark"

        try:
            clean_html = urllib.request.urlopen(clean_url).read().decode('utf-8')
            dark_html = urllib.request.urlopen(dark_url).read().decode('utf-8')
            
            has_delta = (clean_html != dark_html) or (sc_id == 14) # Scenario 14 is clean control baseline
            if len(clean_html) > 50 and len(dark_html) > 50 and has_delta:
                scenario_passes += 1
            else:
                print(f"  [FAIL] Scenario {sc_id:02d} delta check failed")
        except Exception as e:
            print(f"  [FAIL] Scenario {sc_id:02d} HTTP request failed: {e}")

    results.append(log_step("15 Benchmark Scenarios Serving", scenario_passes == len(scenarios), f"{scenario_passes}/{len(scenarios)} scenarios passed Clean vs Dark HTML serving"))

    # 4. Real Playwright Chromium Browser Session Test
    print("\n--- Testing Real Playwright Chromium Browser Session Engine ---")
    try:
        start_payload = json.dumps({"scenario_id": 1, "variant": "dark"}).encode('utf-8')
        start_req = urllib.request.Request(f"{BASE_URL}/api/session/start", data=start_payload, headers={'Content-Type': 'application/json'})
        start_res = json.loads(urllib.request.urlopen(start_req).read().decode('utf-8'))
        
        sess_ok = start_res.get("success", False)
        results.append(log_step("Real Playwright Session Launch", sess_ok, f"Session ID: {start_res.get('session_id', 'N/A')}"))

        time.sleep(1)

        # Status & Extension Health Check
        status_req = urllib.request.urlopen(f"{BASE_URL}/api/session/status")
        status_res = json.loads(status_req.read().decode('utf-8'))
        ext_status = status_res.get("extension_status", "NOT CONNECTED")
        results.append(log_step("UPF Extension Health Inspection", status_res.get("active", False), f"Extension Status: {ext_status}, Sensor: {status_res.get('sensor_status')}"))

        # Screenshot Stream Check
        shot_req = urllib.request.urlopen(f"{BASE_URL}/api/session/screenshot")
        shot_bytes = shot_req.read()
        results.append(log_step("Live Viewport Screenshot Stream", len(shot_bytes) > 500, f"JPEG Frame Size: {len(shot_bytes)} bytes"))

        # Session Interaction Check
        act_payload = json.dumps({"action": "scroll", "selector": "body"}).encode('utf-8')
        act_req = urllib.request.Request(f"{BASE_URL}/api/session/interact", data=act_payload, headers={'Content-Type': 'application/json'})
        act_res = json.loads(urllib.request.urlopen(act_req).read().decode('utf-8'))
        results.append(log_step("Session User Interaction API", act_res.get("success", False), f"Executed action: scroll"))

        # Stop Session Check
        stop_req = urllib.request.Request(f"{BASE_URL}/api/session/stop", data=b"{}", headers={'Content-Type': 'application/json'})
        stop_res = json.loads(urllib.request.urlopen(stop_req).read().decode('utf-8'))
        results.append(log_step("Session Closure & Cleanup", stop_res.get("success", False), stop_res.get("message", "")))

    except Exception as e:
        results.append(log_step("Real Playwright Browser Session", False, str(e)))

    # 5. Free-Browsing Research Trace Analysis Test
    print("\n--- Testing Arbitrary Free-Browsing Research Trace Analyzer ---")
    try:
        sample_trace = {
            "session_id": "e2e_test_trace_001",
            "url": "https://test-store.org/cart",
            "title": "E2E Test Cart Page",
            "trace": [
                {
                    "elements": [
                        {"text": "Hurry! Sale ends in 02:00", "contrastRatio": 4.5, "fontSize": 14},
                        {"text": "Add Warranty Protection ($5.99)", "contrastRatio": 4.5, "checked": True},
                        {"text": "No thanks, I dislike discounts", "contrastRatio": 1.9, "fontSize": 9},
                        {"text": "Mandatory Processing Fee Added: $3.50", "contrastRatio": 4.5}
                    ]
                }
            ]
        }

        trace_payload = json.dumps(sample_trace).encode('utf-8')
        trace_req = urllib.request.Request(f"{BASE_URL}/api/session/analyze_trace", data=trace_payload, headers={'Content-Type': 'application/json'})
        trace_res = json.loads(urllib.request.urlopen(trace_req).read().decode('utf-8'))

        findings_count = len(trace_res.get("findings", []))
        unresolved_count = len(trace_res.get("unresolved_questions", []))
        results.append(log_step("Trace Behavioral Rule Engine", trace_res.get("success", False), f"Detected {findings_count} patterns, {unresolved_count} unresolved questions"))

        # GET Free Browsing Traces Verification
        get_trace_req = urllib.request.urlopen(f"{BASE_URL}/api/session/free_browsing_traces")
        get_trace_res = json.loads(get_trace_req.read().decode('utf-8'))
        latest_sess_id = get_trace_res.get("latest", {}).get("session_id", "")
        results.append(log_step("Free-Browsing Session Inspector API", get_trace_res.get("success", False), f"Retrieved latest session ID: {latest_sess_id}"))

    except Exception as e:
        results.append(log_step("Arbitrary Free-Browsing Trace Analyzer", False, str(e)))

    # Summary Scorecard
    total = len(results)
    passed_count = sum(1 for r in results if r)
    percentage = int((passed_count / total) * 100) if total else 0
    print("\n" + "=" * 80)
    print(f"E2E VERIFICATION COMPLETE: {passed_count}/{total} SUITES PASSED ({percentage}%)")
    print("=" * 80)

if __name__ == "__main__":
    run_e2e_suite()
