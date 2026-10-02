"""
Comprehensive API & Multi-Modal Test Suite for Dark Pattern Detector Backend.
Tests POST /detect with DOM only, Screenshot only, Audio only, and Fused modalities.
Verifies response schemas, threshold filtering, and legacy endpoint compatibility.
"""

import json
import sys
import base64
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

PASS = "PASS"
FAIL = "FAIL"

test_results = []

def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    print(f"  [{status}]  {name}")
    if detail:
        print(f"            {detail}")
    test_results.append(condition)

def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}", timeout=5)
    return json.loads(r.read())

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    r = urllib.request.urlopen(req, timeout=5)
    return json.loads(r.read())

print("\n" + "=" * 60)
print("   Multi-Modal Dark Pattern Detector - API Test Suite")
print("=" * 60)

# 1. Health Checks
print("\n[1] Health & System Info Endpoints")
try:
    h = get("/health")
    test("GET /health status is healthy", h.get("status") == "healthy")
    r = get("/")
    test("GET / service info returns ok", r.get("status") == "ok")
    test("GET / lists 7 categories", len(r.get("categories", [])) == 7)
except Exception as e:
    test("Health check reachable", False, str(e))

# 2. DOM Only POST /detect
print("\n[2] POST /detect - DOM Only Modality")
try:
    body = {
        "elements": [
            {
                "id": "dp_elem_101",
                "tag": "span",
                "text": "Only 2 left in stock! Order now!",
                "contrastRatio": 4.5
            },
            {
                "id": "dp_elem_102",
                "tag": "button",
                "text": "No thanks, I prefer paying full price",
                "contrastRatio": 1.9
            }
        ],
        "url": "https://test-shop.com",
        "threshold": 0.50
    }
    resp = post("/detect", body)
    test("Response contains 'findings'", "findings" in resp)
    test("Dark pattern count > 0", resp.get("dark_patterns_count", 0) > 0)
    test("Modalities processed includes 'dom'", "dom" in resp.get("modalities_processed", []))
    
    findings = resp.get("findings", [])
    if findings:
        f = findings[0]
        test("Finding contains category, confidence, modalities, evidence", 
             all(k in f for k in ["category", "confidence", "modalities", "evidence"]))
except Exception as e:
    test("DOM only detect failed", False, str(e))

# 3. Screenshot Only POST /detect
print("\n[3] POST /detect - Vision Only Modality")
try:
    dummy_png_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
    body = {
        "screenshot_base64": dummy_png_b64,
        "url": "https://test-vision.com"
    }
    resp = post("/detect", body)
    test("Screenshot payload processed", "findings" in resp)
    test("Modalities processed includes 'vision'", "vision" in resp.get("modalities_processed", []))
except Exception as e:
    test("Vision only detect failed", False, str(e))

# 4. Audio Only POST /detect
print("\n[4] POST /detect - Voice Only Modality")
try:
    dummy_wav_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
    body = {
        "audio_base64": dummy_wav_b64,
        "url": "https://test-voice.com"
    }
    resp = post("/detect", body)
    test("Audio payload processed", "findings" in resp)
    test("Modalities processed includes 'voice'", "voice" in resp.get("modalities_processed", []))
except Exception as e:
    test("Voice only detect failed", False, str(e))

# 5. Multi-Modal Fusion POST /detect
print("\n[5] POST /detect - Fused DOM + Vision + Voice")
try:
    body = {
        "elements": [
            {"id": "dp_elem_501", "text": "Hurry! Limited time offer ends soon!"}
        ],
        "screenshot_base64": dummy_png_b64,
        "audio_base64": dummy_wav_b64,
        "url": "https://test-multimodal.com",
        "threshold": 0.50
    }
    resp = post("/detect", body)
    test("All 3 modalities processed", len(resp.get("modalities_processed", [])) == 3)
    test("Findings correctly fused", isinstance(resp.get("findings"), list))
except Exception as e:
    test("Multi-modal fusion failed", False, str(e))

# 6. Legacy /predict compatibility
print("\n[6] Legacy /predict Compatibility Endpoint")
try:
    body = {
        "texts": ["Only 1 item remaining!"],
        "url": "https://test-legacy.com"
    }
    resp = post("/predict", body)
    test("Legacy response format has 'predictions'", "predictions" in resp)
    test("Legacy dark_count key present", "dark_count" in resp)
except Exception as e:
    test("Legacy predict compatibility failed", False, str(e))

# Summary
passed = sum(test_results)
total = len(test_results)
print("\n" + "=" * 60)
print(f"   API Test Result: {passed}/{total} tests passed")
print("=" * 60 + "\n")

sys.exit(0 if passed == total else 1)
