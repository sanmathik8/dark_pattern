# WORK_PROGRESS.md — Dark Pattern Project Work & Verification Status

## Project Overview
**Dark Pattern** (also referred to as **Universal Pattern Finder / UPF**) is a behavioral research platform and detection engine designed to identify deceptive dark patterns in web applications. It combines a Chrome Extension DOM Sensor, a Playwright Chromium Real Browser Session Manager, a Multi-Application Observatory Server (Port 8080), a Multimodal Backend Detection API (Flask), and dynamic stateful analysis pipelines.

---

## A. Work Completed

### 1. Chrome Extension (UPF DOM Sensor)
- **Manifest V3 Extension**: Loaded from `extension/` containing `manifest.json`, `content.js`, `background.js`, `popup.html`, `popup.css`, and `popup.js`.
- **Universal DOM Sensor (`extension/content.js`)**: Real-time DOM mutation monitoring, contrast ratio calculation, font size inspection, pre-checked element detection, and timer observation.
- **Background Event Handler (`extension/background.js`)**: Background service worker buffering trace events and communicating with backend endpoints (`http://localhost:8080` and `http://localhost:5000`).
- **Live Extension Popup UI (`extension/popup.html`, `popup.css`, `popup.js`)**: Interactive UI with Dribbble-inspired styling (`#020202`, `#0FB8F8`, `#EBECF0`), live status badges (`NOT CONNECTED`, `SCANNING`, `ACTIVE`), session toggle button, free-browsing trace timeline, findings list, and an event-driven **Live Behavioral Analysis Pipeline Graph** displaying 8 stages and verdict badges (`SUPPORTED`, `POTENTIAL`, `NO EVIDENCE`, `INCONCLUSIVE`).

### 2. Research Observatory Server (`simulator/run_scenarios.py`)
- **Port 8080 Server**: HTTP server handling scenario applications, manifest delivery (`/manifest.json`), live browser screenshot streams (`/api/session/screenshot`), session lifecycle APIs (`/api/session/start`, `/api/session/status`, `/api/session/stop`, `/api/session/interact`), trace analysis (`/api/session/analyze_trace`), and extension detection endpoint (`/detect`).
- **15 Dynamic Scenarios**: Data-driven scenario management across 15 categories (Scarcity, Late Fees, Pre-selected Extras, Forced Continuity, Confirmshaming, Visual Interference, Obstruction, Trick Questions, Nagging, Hard to Cancel, Drip Pricing, Disguised Ads, Hidden Subscription, Bait & Switch, Clean Baseline Control). Supports both Clean and Dark variants.
- **Observatory Platform Dashboard (`simulator/checker.html`)**: Web interface featuring scenario gallery, variant toggles, live Playwright screenshot streaming, workspace interaction controls, 8-stage live pipeline visualization graph, and trace timelines.

### 3. Real Browser Session Management (`simulator/core/`)
- **Thread-Safe Playwright Manager (`simulator/core/browser.py`)**: `BrowserSession` class running on a dedicated single-threaded dispatcher (`BrowserThreadDispatcher`) to guarantee Playwright greenlet safety. Launches persistent Chromium contexts loaded with the local UPF extension.
- **Environment Managers (`simulator/core/environment.py`, `git_environment.py`)**: Manages scenario serving from local curated HTML fixtures and isolated Git checkouts (`runtime/`).

### 4. Multimodal Backend Detection Engine (`backend/`)
- **Flask API (`backend/app.py`)**: Port 5000 backend providing `/detect`, `/api/analyze_text`, `/api/analyze_image`, `/api/analyze_voice`, `/api/fusion`, `/api/flow`, `/api/legal`, and `/api/report`.
- **Text Classifier (`backend/text_branch.py`)**: DistilBERT transformer model (`model/distilbert_dark_pattern`) with linear SVM fallback (`model/linear_svm.pkl`) and heuristic rule regexes for text classification.
- **Evidence Fusion Engine (`backend/fusion.py`)**: Merges text, DOM, vision, and state transition signals into unified pattern confidence scores.
- **Legal Compliance Engine (`backend/legal_engine.py`)**: Maps detected patterns against India CCPA Guidelines 2023 and Consumer Protection Act 2019 legal citations.
- **Stateful Flow Tracker (`backend/flow_engine.py`)**: Tracks multi-step user navigation sessions.

### 5. Automated E2E Verification & Audit Suite (`simulator/`)
- **`simulator/e2e_real_browser_test.py`**: Real Playwright Chromium end-to-end test suite verifying the complete pipeline: `REAL USER ACTION -> EXTENSION EVENT -> BEFORE/AFTER STATE -> BEHAVIORAL DIFF -> EVIDENCE -> PATTERN -> VERDICT -> LIVE GRAPH`.
- **Blind Test Scripts (`simulator/blind_realworld_audit.py`, `blind_positive_test.py`, `realworld_external_positive_search.py`)**: Zero-knowledge test scripts executing Any Website Mode testing against local applications and live public internet targets (`https://httpbin.org/forms/post`, `https://saucedemo.com`, `https://demo.playwright.dev/todomvc/`).

---

## B. Work Partially Completed

1. **Vision Branch (`backend/image_branch.py`)**:
   - Structural implementation exists for image processing and screenshot analysis.
   - External vision API calls (OpenAI/Gemini/Anthropic) are currently stubbed/placeholder functions fallbacking to DOM/text analysis when vision API keys are omitted.

2. **Voice Branch (`backend/voice_branch.py`)**:
   - Audio file upload and transcription pipeline structures exist.
   - Speech-to-text / audio pattern detection is partially implemented with mock signal placeholders.

3. **Git Checkout Environment Manager (`simulator/core/git_environment.py`)**:
   - Clones and builds remote GitHub scenario repositories into `runtime/`.
   - Fallbacks to local curated fixture HTML when node/npm build dependencies fail in isolated subshell environments.

---

## C. Work Remaining

1. Integration of live multimodal LLM vision APIs into `image_branch.py`.
2. Full Whisper / STT integration for `voice_branch.py`.
3. Standalone Docker containerization for production deployment.

---

## D. Verification Status

### Tests Executed & Results:

1. **Real Browser End-to-End Test (`simulator/e2e_real_browser_test.py`)**:
   - **Command**: `python simulator/e2e_real_browser_test.py`
   - **Status**: **PASSED** (Code 0)
   - **Verified**: Real Playwright Chromium launch with extension, DOM state before/after capture (`checked=true` -> `checked=false`), behavioral diff calculation, 8-stage pipeline stage execution, and all 4 verdict states (`SUPPORTED`, `POTENTIAL`, `NO EVIDENCE`, `INCONCLUSIVE`).

2. **External Negative Control Test (`simulator/blind_realworld_audit_external.py`)**:
   - **Command**: `python simulator/blind_realworld_audit_external.py`
   - **Target**: `https://httpbin.org/forms/post` (Public Live Website)
   - **Status**: **PASSED** (Code 0)
   - **Verdict**: `NO EVIDENCE` (0 false positives).

3. **Public Internet Target Blind Test (`simulator/realworld_external_positive_search.py`)**:
   - **Command**: `python simulator/realworld_external_positive_search.py`
   - **Target**: `https://demo.playwright.dev/todomvc/` (Playwright TodoMVC Public Benchmark)
   - **Status**: **PASSED** (Code 0)
   - **Result**: Frozen before ground truth reveal to `results/blind_external_positive_20261002_155913.json`. Verdict: `NO EVIDENCE` (Clean baseline verified).

---

## E. Important Assumptions or Unknowns

1. **External LLM Dependencies**: The core behavioral engine operates deterministically using DOM properties, state mutations, and text rules. External LLM services (Gemini/OpenAI) are optional and not required for core platform functionality.
2. **Browser Context**: Real browser testing requires Playwright Chromium and Windows/Linux graphical environment support or headless Xvfb configuration.
