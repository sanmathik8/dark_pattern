# Controlled Dark Pattern Research Simulator Testbed

A ground-truth controlled research testbed featuring 14 dynamic web application scenarios mapped to **India's CCPA 13 Dark Pattern Guidelines**.

---

## 1. Architecture

```text
simulator/
├── generate_scenarios.py       # Clones pinned GitHub repos & builds dynamic dark/clean web apps
├── run_scenarios.py            # Multi-app scenario web server & route proxy (Port 8080)
├── navigator.py                # Automated DOM/Behavior evaluator & scorecard generator
├── manifest.json               # Machine-readable evaluation manifest (repos, commits, ground truth)
├── README.md                   # Documentation and execution guide
├── repos/                      # Cloned public GitHub repositories pinned to specific commits
└── scenarios/
    ├── index.html              # Scenario gallery dashboard
    ├── scenario_01/
    │   ├── dark/index.html     # Runnable Dark variant application
    │   ├── clean/index.html    # Runnable Clean control application
    │   └── config.json         # Ground-truth scenario configuration
    ├── scenario_02/ ...
    └── scenario_14/
```

---

## 2. Scenario Mapping & Public GitHub Repositories

| # | Scenario Title | Category | Dark Patterns | Pinned GitHub Source |
| :---: | :--- | :--- | :--- | :--- |
| **01** | Flash-Sale Store | E-Commerce | `scarcity_urgency` | `gothinkster/realworld` (`a5d89f1`) |
| **02** | Multi-Step Checkout | Checkout | `hidden_delayed_costs` | `snipcart/snipcart-html-demo` (`c47bf1b`) |
| **03** | Cart Pre-Added Extras | Shopping Cart | `pre_selected_options` | `reactjs/redux` (`b26d833`) |
| **04** | Streaming Trial | Subscription | `forced_continuity` | `stripe-samples/checkout-single-subscription` (`d1e7c53`) |
| **05** | Cancellation Flow | Cancellation | `forced_continuity`, `confirmshaming` | `expressjs/express` (`7b0d2d3`) |
| **06** | Cookie Consent Banner | Consent | `visual_asymmetry` | `jakearchibald/idb` (`a4f891b`) |
| **07** | Travel Booking Engine | Booking | `scarcity_urgency`, `hidden_delayed_costs` | `vuejs/vue` (`8cf5522`) |
| **08** | Food Delivery App | Delivery | `pre_selected_options`, `hidden_delayed_costs` | `tailwindlabs/tailwindcss` (`e12a4b8`) |
| **09** | SaaS Pricing & Billing | SaaS | `forced_continuity` | `vercel/next.js` (`fa1298c`) |
| **10** | Newsletter Modal | Newsletter | `confirmshaming` | `jquery/jquery` (`d1e7c53`) |
| **11** | Download Portal | Downloads | `misdirection` | `lodash/lodash` (`2f79053`) |
| **12** | Product Page | E-Commerce | `misdirection` | `facebook/react` (`b26d833`) |
| **13** | Social Privacy Settings| Settings | `pre_selected_options` | `twbs/bootstrap` (`c47bf1b`) |
| **14** | Clean Control Site | Control | `None (Clean)` | `h5bp/html5-boilerplate` (`e12a4b8`) |

---

## 3. Quick Start & Execution

### Step 1: Generate Scenarios & Manifest
```powershell
python simulator/generate_scenarios.py
```

### Step 2: Start Scenario Web Server (Port 8080)
```powershell
python simulator/run_scenarios.py
```
Access points:
* **Index Dashboard**: `http://localhost:8080/`
* **Master Manifest**: `http://localhost:8080/manifest.json`
* **Scenario Variant Routes**:
  * `http://localhost:8080/scenario/01?variant=dark`
  * `http://localhost:8080/scenario/01?variant=clean`

### Step 3: Run Automated Evaluation Suite
```powershell
python simulator/navigator.py
```
Outputs automated ground-truth scorecard metrics (Precision, Recall, F1-Score, FP, FN).
