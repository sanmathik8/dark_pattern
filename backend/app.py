"""
Multi-Modal & Stateful Dark Pattern Detector — FastAPI Backend
Combines Behavioral Flow Engine, DOM/Text analysis, Screenshot/Vision analysis (optional),
Audio/Voice analysis (optional), Evidence-Aware Fusion, Legal Compliance Engine, and Dashboard API.
Categories:
1. scarcity_urgency
2. pre_selected_options
3. visual_asymmetry
4. confirmshaming
5. hidden_delayed_costs
6. forced_continuity
7. misdirection
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import joblib
import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from backend.text_branch import analyze_text_and_dom, CATEGORIES
from backend.image_branch import analyze_screenshot
from backend.voice_branch import analyze_audio
from backend.flow_engine import analyze_state_transition
from backend.fusion import fuse_multimodal_findings
from backend.legal_engine import enrich_finding_with_legal_compliance, calculate_risk_assessment
from backend.image_annotator import annotate_screenshot
from backend.report_generator import generate_audit_report_html

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("dark-pattern-backend")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Stateful Multi-Modal Dark Pattern Detector API",
    description="Detects dark patterns using Stateful Web-Flow Analysis, DOM, Vision, Voice, and Fusion.",
    version="3.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Model paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
TRANSFORMER_MODEL_DIR = BASE_DIR / "model" / "distilbert_dark_pattern"
SVM_MODEL_PATH = BASE_DIR / "model" / "linear_svm.pkl"
DASHBOARD_HTML_PATH = BASE_DIR / "backend" / "dashboard.html"

model_bundle: dict = {}

@app.on_event("startup")
def load_models():
    global model_bundle
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 1. Try DistilBERT Multi-label model
    if TRANSFORMER_MODEL_DIR.exists() and (TRANSFORMER_MODEL_DIR / "config.json").exists():
        log.info(f"Loading DistilBERT multi-label model from {TRANSFORMER_MODEL_DIR} ...")
        try:
            tokenizer = AutoTokenizer.from_pretrained(str(TRANSFORMER_MODEL_DIR))
            model = AutoModelForSequenceClassification.from_pretrained(
                str(TRANSFORMER_MODEL_DIR),
                num_labels=len(CATEGORIES),
                problem_type="multi_label_classification",
                ignore_mismatched_sizes=True
            )
            model.to(device)
            model.eval()

            model_bundle["type"] = "transformer"
            model_bundle["model"] = model
            model_bundle["tokenizer"] = tokenizer
            model_bundle["device"] = device
            model_bundle["model_name"] = "distilbert_dark_pattern"
            log.info(f"DistilBERT multi-label model loaded on device: {device}")
            return
        except Exception as e:
            log.error(f"Failed to load DistilBERT model: {e}. Falling back to Linear SVM.")

    # 2. Try Linear SVM Multi-label Fallback
    if SVM_MODEL_PATH.exists():
        log.info(f"Loading Linear SVM model from {SVM_MODEL_PATH} ...")
        try:
            bundle = joblib.load(SVM_MODEL_PATH)
            model_bundle["type"] = "linear_svm"
            model_bundle["classifier"] = bundle["classifier"]
            model_bundle["vectorizer"] = bundle["vectorizer"]
            model_bundle["model_name"] = bundle.get("model_name", "linear_svm")
            log.info("Linear SVM multi-label model loaded successfully.")
        except Exception as e:
            log.error(f"Failed to load Linear SVM model: {e}")
    else:
        log.warning("No trained ML model files found! Will rely on DOM/Behavioral heuristics.")

# ── Request / Response Schemas ────────────────────────────────────────────────
class DOMElementItem(BaseModel):
    id: str
    tag: Optional[str] = ""
    role: Optional[str] = ""
    text: Optional[str] = ""
    ariaLabel: Optional[str] = None
    placeholder: Optional[str] = None
    fontSize: Optional[float] = None
    fontWeight: Optional[Any] = None
    color: Optional[str] = None
    backgroundColor: Optional[str] = None
    contrastRatio: Optional[float] = None
    checked: Optional[bool] = False
    hidden: Optional[bool] = False
    rect: Optional[Dict[str, Any]] = None

class UserActionItem(BaseModel):
    type: Optional[str] = "navigation"
    target_id: Optional[str] = "dp_elem_action"
    text: Optional[str] = ""

class DetectRequest(BaseModel):
    elements: Optional[List[DOMElementItem]] = Field(default_factory=list)
    texts: Optional[List[str]] = Field(default_factory=list)
    screenshot_base64: Optional[str] = ""
    audio_base64: Optional[str] = ""
    user_action: Optional[UserActionItem] = None
    state_before: Optional[Dict[str, Any]] = None
    state_after: Optional[Dict[str, Any]] = None
    url: Optional[str] = ""
    threshold: Optional[float] = 0.50

class FusedFindingItem(BaseModel):
    category: str
    confidence: float
    modalities: List[str]
    element_id: Optional[str] = None
    bbox: Optional[List[int]] = None
    rect: Optional[Dict[str, Any]] = None
    evidence: List[str]
    reason: str
    legal_info: Optional[Dict[str, Any]] = None
    severity: Optional[str] = "MEDIUM"
    state_transition: Optional[Dict[str, Any]] = None

class DetectResponse(BaseModel):
    findings: List[FusedFindingItem]
    total_elements_scanned: int
    dark_patterns_count: int
    risk_assessment: Dict[str, Any]
    annotated_screenshot: Optional[str] = ""
    url: str
    model_type: str
    modalities_processed: List[str]


MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_BYTES = 25 * 1024 * 1024       # 25 MB

def validate_payload_size(req: DetectRequest):
    if req.screenshot_base64 and len(req.screenshot_base64) > MAX_SCREENSHOT_BYTES * 1.4:
        raise HTTPException(status_code=413, detail="Screenshot payload exceeds 10MB limit")
    if req.audio_base64 and len(req.audio_base64) > MAX_AUDIO_BYTES * 1.4:
        raise HTTPException(status_code=413, detail="Audio payload exceeds 25MB limit")


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Stateful Multi-Modal Dark Pattern Detector",
        "version": "3.5.0",
        "dashboard_url": "/dashboard",
        "model_loaded": bool(model_bundle),
        "model_type": model_bundle.get("type", "heuristic_fallback"),
        "categories": CATEGORIES
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": bool(model_bundle),
        "model_type": model_bundle.get("type", "heuristic_fallback"),
    }

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    if DASHBOARD_HTML_PATH.exists():
        with open(DASHBOARD_HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard UI Not Found</h1>"

@app.post("/detect", response_model=DetectResponse)
def detect(req: DetectRequest):
    validate_payload_size(req)

    modalities_processed = []

    elements_dict = []
    if req.elements:
        elements_dict = [el.model_dump() for el in req.elements]
    elif req.texts:
        elements_dict = [{"id": f"dp_elem_{idx}", "text": txt} for idx, txt in enumerate(req.texts)]

    # 1. Behavioral Flow State Transition Branch
    behavioral_findings = []
    if req.state_before and req.state_after:
        action_dict = req.user_action.model_dump() if req.user_action else None
        behavioral_findings = analyze_state_transition(
            req.state_before, req.state_after, action_dict, req.threshold
        )
        if behavioral_findings:
            modalities_processed.append("behavioral")

    # 2. DOM / Text Branch
    dom_findings = []
    if elements_dict:
        dom_findings = analyze_text_and_dom(elements_dict, model_bundle, req.threshold)
        modalities_processed.append("dom")

    # 3. Screenshot / Vision Branch (Optional)
    vision_findings = []
    if req.screenshot_base64:
        vision_findings = analyze_screenshot(req.screenshot_base64, req.threshold)
        modalities_processed.append("vision")

    # 4. Voice / Audio Branch (Optional)
    voice_findings = []
    if req.audio_base64:
        voice_findings = analyze_audio(req.audio_base64, model_bundle, req.threshold)
        modalities_processed.append("voice")

    # 5. Multi-Modal Evidence Fusion (Integrates Behavioral + DOM + Vision + Voice)
    fused_findings = fuse_multimodal_findings(
        dom_findings=dom_findings,
        vision_findings=vision_findings,
        voice_findings=voice_findings,
        behavioral_findings=behavioral_findings,
        threshold=req.threshold
    )

    # 6. Enrich findings with Legal Compliance Citations
    enriched_findings = [enrich_finding_with_legal_compliance(f) for f in fused_findings]
    risk_assessment = calculate_risk_assessment(enriched_findings)

    # 7. Optional screenshot annotation overlay
    annotated_img = ""
    if req.screenshot_base64 and enriched_findings:
        annotated_img = annotate_screenshot(req.screenshot_base64, enriched_findings)

    formatted_findings = [FusedFindingItem(**item) for item in enriched_findings]

    return DetectResponse(
        findings=formatted_findings,
        total_elements_scanned=len(elements_dict),
        dark_patterns_count=len(formatted_findings),
        risk_assessment=risk_assessment,
        annotated_screenshot=annotated_img,
        url=req.url or "",
        model_type=model_bundle.get("type", "heuristic_fallback"),
        modalities_processed=modalities_processed
    )


@app.post("/report", response_class=HTMLResponse)
def generate_report(req: DetectRequest):
    detect_res = detect(req)
    report_html = generate_audit_report_html(detect_res.model_dump())
    return HTMLResponse(content=report_html)


@app.post("/predict")
def legacy_predict(req: Dict[str, Any]):
    texts = req.get("texts", [])
    url = req.get("url", "")
    
    detect_req = DetectRequest(texts=texts, url=url, threshold=0.50)
    res = detect(detect_req)

    legacy_predictions = []
    for f in res.findings:
        legacy_predictions.append({
            "text": f.evidence[0] if f.evidence else "",
            "label": 1,
            "category": f.category,
            "confidence": f.confidence,
            "detected": True,
            "element_id": f.element_id,
            "legal_info": f.legal_info
        })

    return {
        "predictions": legacy_predictions,
        "url": url,
        "total": len(texts),
        "dark_count": len(legacy_predictions),
        "model": res.model_type
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
