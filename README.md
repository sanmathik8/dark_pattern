# Dark Pattern — Deceptive Pattern Research & Detection Platform

## Overview
**Dark Pattern** (also known as **Universal Pattern Finder / UPF**) is a behavioral research platform and multi-modal detection system designed to inspect, analyze, and document deceptive user interface patterns in web applications. The system combines a Chrome Extension DOM Sensor, a Playwright Chromium Browser Session Engine, a Multi-Application Research Observatory Server, and a Backend Detection API.

---

## Problem Statement
E-commerce websites and digital services frequently employ dark patterns—interface designs that trick or manipulate users into making decisions they might not otherwise make (such as pre-selected add-ons, hidden service fees, deceptive urgency timers, and difficult cancellation flows). Detecting these behaviors requires observing dynamic DOM mutations, user actions, and state transitions over time rather than inspecting static web page text alone.

---

## Current Implementation
The repository currently contains:
- **UPF Chrome Extension (`extension/`)**: Manifest V3 extension with a DOM sensor (`content.js`), background service worker (`background.js`), and popup interface (`popup.js`) featuring an 8-stage **Live Behavioral Analysis Pipeline Graph** and verdict indicators (`SUPPORTED`, `POTENTIAL`, `NO EVIDENCE`, `INCONCLUSIVE`).
- **Research Observatory Server (`simulator/run_scenarios.py`)**: Port 8080 HTTP server serving 15 dynamic scenario applications with Dark and Clean variants, scenario registry (`/manifest.json`), browser screenshot streams, and trace analysis APIs (`/api/session/analyze_trace`).
- **Real Browser Manager (`simulator/core/browser.py`)**: Thread-safe Playwright Chromium browser manager running persistent Chromium contexts with the UPF extension loaded.
- **Backend Detection Engine (`backend/`)**: Flask API (Port 5000) providing text classification, evidence fusion, legal mapping (India CCPA Dark Pattern Guidelines 2023 & Consumer Protection Act 2019), and report generation.
- **E2E & Audit Suite (`simulator/`)**: Automated Playwright test scripts for end-to-end pipeline verification and zero-knowledge blind testing in Any Website Mode.

---

## Technology Stack
- **Languages**: Python 3.10+, JavaScript (ES6+), HTML5, CSS3
- **Browser Automation**: Playwright (Python Sync API)
- **Extension**: Chrome Extension API (Manifest V3)
- **Backend Framework**: Flask, Python `http.server`
- **Machine Learning & NLP**: PyTorch, Transformers (DistilBERT), Scikit-Learn (Linear SVM), NLTK, Pandas
- **Testing**: Pytest, Custom Playwright E2E Runner

---

## Project Structure
```
dark_pattern/
├── backend/                  # Flask detection backend API & multimodal branches
│   ├── app.py                # Main backend server entry point
│   ├── text_branch.py        # DistilBERT & Linear SVM text classifier
│   ├── image_branch.py       # Vision branch structure (stubbed vision API)
│   ├── voice_branch.py       # Audio branch structure (stubbed audio API)
│   ├── fusion.py             # Multimodal evidence fusion engine
│   ├── legal_engine.py       # India CCPA & CPA 2019 regulatory mapper
│   ├── flow_engine.py        # Stateful user journey session tracker
│   └── dashboard.html        # Backend analytics dashboard
├── extension/                # Manifest V3 Chrome Extension (UPF Sensor)
│   ├── manifest.json         # Extension configuration
│   ├── content.js            # DOM sensor & interaction observer
│   ├── background.js         # Service worker & trace buffer
│   ├── popup.html            # Extension popup layout
│   ├── popup.css             # Extension styling (Dribbble dark theme)
│   └── popup.js              # Live analysis pipeline graph renderer
├── simulator/                # Research Observatory & Playwright Environment
│   ├── run_scenarios.py      # Observatory server (Port 8080)
│   ├── checker.html          # Observatory platform web UI
│   ├── manifest.json         # 15 scenario registry definitions
│   ├── core/
│   │   ├── browser.py        # Thread-safe Playwright Chromium manager
│   │   ├── environment.py    # Fixture environment manager
│   │   └── git_environment.py# Git repository checkout manager
│   ├── e2e_real_browser_test.py # Real browser Playwright E2E suite
│   ├── blind_realworld_audit.py # Local blind audit runner
│   ├── blind_realworld_audit_external.py # Public internet negative control test
│   └── realworld_external_positive_search.py # Zero-knowledge public internet audit
├── model/                    # ML Model Artifacts
│   ├── distilbert_dark_pattern/ # DistilBERT model configuration
│   └── linear_svm.pkl        # Linear SVM fallback classifier
├── results/                  # Evaluation results & audit evidence artifacts
├── WORK_PROGRESS.md          # Comprehensive progress & verification log
└── README.md                 # Project documentation
```

---

## How to Run

### Prerequisites
- Python 3.10 or higher
- Node.js (optional, for running local Node-based scenario checkouts)
- Playwright Chromium installed (`playwright install chromium`)

### 1. Start the Research Observatory Server (Port 8080)
```bash
python simulator/run_scenarios.py
```
Access the Observatory Web Interface at: `http://localhost:8080/`

### 2. Start the Backend Detection Server (Port 5000)
```bash
python backend/app.py
```

### 3. Load the UPF Extension into Chrome / Chromium
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (top right toggle).
3. Click **Load unpacked** and select the `D:\darkpattern\extension` directory.

### 4. Run Automated E2E Verification
```bash
python simulator/e2e_real_browser_test.py
```

---

## Current Status & Limitations
- **Implemented**: Chrome Extension DOM Sensor, 8-stage live pipeline graph, Port 8080 Observatory Server, thread-safe Playwright Chromium context dispatcher, text classification branch, evidence fusion engine, CCPA legal mapping, and automated E2E test scripts.
- **Incomplete / Stubbed Limitations**:
  - Image Vision Branch (`backend/image_branch.py`): External vision LLM API calls are stubbed placeholders; visual element detection currently fallbacks to DOM/text analysis.
  - Voice Audio Branch (`backend/voice_branch.py`): Speech-to-text transcription is stubbed with mock signal placeholders.
- **Under Development**: Production Docker containerization and live vision API integrations.

---

## Testing
- **Real Browser E2E Test (`simulator/e2e_real_browser_test.py`)**: Executed and verified cleanly against live Playwright Chromium. Validates real user click actions, before/after state captures (`checked=true` -> `checked=false`), behavioral deltas, 8-stage live analysis graph execution, and verdict states (`SUPPORTED`, `POTENTIAL`, `NO EVIDENCE`, `INCONCLUSIVE`).
- **External Public Audit (`simulator/blind_realworld_audit_external.py` & `realworld_external_positive_search.py`)**: Executed against public internet targets (`https://httpbin.org/forms/post`, `https://demo.playwright.dev/todomvc/`). Verified zero false positives (`NO EVIDENCE`).

---

## Future & Remaining Work
1. Live multimodal LLM vision API integration for `backend/image_branch.py`.
2. Whisper STT audio pipeline integration for `backend/voice_branch.py`.
3. Standalone Docker containerization for production deployment.
4. Expanded benchmark suite for mobile web view interfaces.
