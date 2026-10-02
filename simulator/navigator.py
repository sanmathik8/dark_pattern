"""
Automated Navigator & Evaluation Agent for Dark Pattern Simulator
Evaluates 14 Scenarios across Dark and Clean variants against ground truth configs.
Calculates Precision, Recall, F1-Score, False Positives, and False Negatives.
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
CONFIGS_PATH = BASE_DIR / "scenarios" / "configs.json"
SCENARIOS_DIR = BASE_DIR / "scenarios"
API_URL = "http://127.0.0.1:8000/detect"

def extract_elements_from_html(html_str: str):
    """Parses static scenario HTML to produce scraped DOM elements list."""
    soup = BeautifulSoup(html_str, "html.parser")
    elements = []
    texts = []
    
    counter = 100
    for tag in soup.find_all(['button', 'input', 'a', 'p', 'h1', 'h2', 'h3', 'div', 'span', 'label']):
        text = tag.get_text(strip=True)
        if not text and not tag.get("checked"):
            continue
            
        counter += 1
        elem_id = f"dp_elem_{counter}"
        tag_name = tag.name
        is_checked = tag.has_attr("checked") or tag.get("aria-checked") == "true"
        
        # Calculate contrast ratio approximation
        contrast = 4.5
        style = tag.get("style", "")
        if "color:#aaa" in style or "color:#888" in style or "font-size:10px" in style or "font-size:9px" in style:
            contrast = 1.9

        elements.append({
            "id": elem_id,
            "tag": tag_name,
            "role": tag.get("role", ""),
            "text": text[:300],
            "checked": is_checked,
            "contrastRatio": contrast,
            "fontSize": 14 if "font-size:10px" not in style else 10,
            "rect": {"x": 100, "y": counter * 30, "width": 200, "height": 30}
        })
        if text:
            texts.append(text[:300])
            
    return elements, texts

def run_evaluation_suite():
    print("=" * 80)
    print("   DARK PATTERN DETECTOR — AUTOMATED NAVIGATOR EVALUATION SCORECARD")
    print("=" * 80)
    
    if not CONFIGS_PATH.exists():
        print(f"[ERROR] Configs file not found at {CONFIGS_PATH}")
        return

    with open(CONFIGS_PATH, "r", encoding="utf-8") as f:
        configs = json.load(f)

    tp, fp, fn, tn = 0, 0, 0, 0
    results = []

    for sc in configs:
        for variant in ["dark", "clean"]:
            html_file = SCENARIOS_DIR / f"scenario_{sc['id']}.html"
            if not html_file.exists():
                continue
                
            with open(html_file, "r", encoding="utf-8") as f:
                raw_html = f.read()
                
            # Replace variant placeholder
            variant_html = sc["dark_html"] if variant == "dark" else sc["clean_html"]
            elements, texts = extract_elements_from_html(variant_html)
            
            planted = sc["dark_patterns"] if variant == "dark" else []
            
            # Post to FastAPI backend /detect
            payload = {
                "elements": elements,
                "texts": texts,
                "url": f"http://localhost:8080/scenarios/scenario_{sc['id']}.html?variant={variant}",
                "threshold": 0.50
            }
            
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(API_URL, data=req_data, headers={"Content-Type": "application/json"})
            
            try:
                with urllib.request.urlopen(req) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    findings = res_json.get("findings", [])
            except Exception as e:
                findings = []

            detected_cats = list(set([f["category"] for f in findings]))
            
            # Evaluate against planted ground truth
            if variant == "dark":
                matched = [c for c in detected_cats if c in planted]
                unmatched = [c for c in detected_cats if c not in planted]
                missed = [c for c in planted if c not in detected_cats]
                
                tp += len(matched)
                fp += len(unmatched)
                fn += len(missed)
                
                status = "PASS" if len(missed) == 0 else "PARTIAL/MISS"
            else:
                if len(detected_cats) > 0:
                    fp += len(detected_cats)
                    status = "FALSE POSITIVE"
                else:
                    tn += 1
                    status = "CLEAN PASS"

            results.append({
                "id": sc["id"],
                "title": sc["title"],
                "variant": variant.upper(),
                "planted": planted,
                "detected": detected_cats,
                "status": status
            })

    # Print Formatted Evaluation Matrix
    print(f"\n{'#':<4} | {'Scenario Title':<26} | {'Variant':<8} | {'Planted Ground Truth':<25} | {'Detected Categories':<25} | {'Status'}")
    print("-" * 115)
    for r in results:
        planted_str = ", ".join(r["planted"]) if r["planted"] else "None (Clean)"
        detected_str = ", ".join(r["detected"]) if r["detected"] else "Clean / None"
        print(f"{r['id']:<4} | {r['title']:<26} | {r['variant']:<8} | {planted_str:<25} | {detected_str:<25} | {r['status']}")

    # Calculate Overall Scorecard Metrics
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 100.0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 100.0
    f1 = (2 * precision * recall / (precision + recall)) / 100 if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 80)
    print("   AUTOMATED SCORECARD METRICS SUMMARY")
    print("=" * 80)
    print(f"  • True Positives (TP)  : {tp}")
    print(f"  • False Positives (FP) : {fp}")
    print(f"  • False Negatives (FN) : {fn}")
    print(f"  • True Negatives (TN)  : {tn}")
    print(f"  • Precision            : {precision:.2f}%")
    print(f"  • Recall               : {recall:.2f}%")
    print(f"  • F1-Score             : {f1:.3f}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_evaluation_suite()
