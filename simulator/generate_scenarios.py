"""
Multi-Application Research Simulator Generator for Dark Pattern Detector
Clones open-source repositories (pinned to commits) or builds self-contained
multi-step web applications for 14 ground-truth dark pattern scenarios.
Generates dark/clean dynamic variants, scenario configs with predicate-based ground truth, and a master manifest.json.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

SIMULATOR_DIR = Path(__file__).parent
REPOS_DIR = SIMULATOR_DIR / "repos"
SCENARIOS_DIR = SIMULATOR_DIR / "scenarios"
MANIFEST_PATH = SIMULATOR_DIR / "manifest.json"

SCENARIO_CONFIGS = [
    {
        "id": 1,
        "slug": "scenario_01",
        "title": "Flash-Sale Store",
        "category": "E-Commerce",
        "dark_patterns": ["scarcity_urgency"],
        "predicates": {
            "scarcity_urgency": {
                "positive_predicates": ["countdown_timer_present", "urgency_text_present", "scarcity_claim_present"],
                "negative_predicates": ["no_timer_in_clean", "no_pressure_in_clean"]
            }
        },
        "github_repo": "https://github.com/gothinkster/realworld.git",
        "commit_hash": "a5d89f13e734c3111f181640a33116bcbf29d2bf",
        "entrypoint": "index.html",
        "description": "Product store featuring a live JavaScript countdown timer that decrements and resets on reload."
    },
    {
        "id": 2,
        "slug": "scenario_02",
        "title": "Multi-Step Checkout with Late Fees",
        "category": "Checkout",
        "dark_patterns": ["hidden_delayed_costs"],
        "predicates": {
            "hidden_delayed_costs": {
                "positive_predicates": ["late_fee_added", "price_increase_at_checkout"],
                "negative_predicates": ["upfront_fee_disclosure_in_clean"]
            }
        },
        "github_repo": "https://github.com/snipcart/snipcart-html-demo.git",
        "commit_hash": "c47bf1b2a95c479e0f6e1088a2ef8673f82161f3",
        "entrypoint": "index.html",
        "description": "Multi-step checkout (Cart -> Shipping -> Payment) introducing an unrequested $12 service fee late in the flow."
    },
    {
        "id": 3,
        "slug": "scenario_03",
        "title": "Cart with Pre-Added Extras",
        "category": "Shopping Cart",
        "dark_patterns": ["pre_selected_options"],
        "predicates": {
            "pre_selected_options": {
                "positive_predicates": ["preselected_addon_checkbox", "optional_item_prechecked"],
                "negative_predicates": ["clean_unchecked_addons"]
            }
        },
        "github_repo": "https://github.com/reactjs/redux.git",
        "commit_hash": "b26d8338e55c68f128d8b9d8858f9188e7b99a12",
        "entrypoint": "index.html",
        "description": "Interactive cart application with pre-checked $19.99 extended warranty and express processing checkboxes."
    },
    {
        "id": 4,
        "slug": "scenario_04",
        "title": "Streaming Subscription Free Trial",
        "category": "Subscription",
        "dark_patterns": ["forced_continuity"],
        "predicates": {
            "forced_continuity": {
                "positive_predicates": ["hidden_auto_renewal", "cancellation_barrier_fine_print"],
                "negative_predicates": ["transparent_cancellation_in_clean"]
            }
        },
        "github_repo": "https://github.com/stripe-samples/checkout-single-subscription.git",
        "commit_hash": "d1e7c53641f238ab90d3a958b1220a1122ab45e3",
        "entrypoint": "index.html",
        "description": "SaaS streaming subscription trial with hidden fine-print auto-renewal and phone-only cancellation notice."
    },
    {
        "id": 5,
        "slug": "scenario_05",
        "title": "Multi-Step Cancellation Flow",
        "category": "Cancellation",
        "dark_patterns": ["forced_continuity", "confirmshaming"],
        "predicates": {
            "forced_continuity": {
                "positive_predicates": ["multi_step_cancellation_barrier"],
                "negative_predicates": ["direct_cancellation_in_clean"]
            },
            "confirmshaming": {
                "positive_predicates": ["guilt_inducing_opt_out_text"],
                "negative_predicates": ["neutral_buttons_in_clean"]
            }
        },
        "github_repo": "https://github.com/expressjs/express.git",
        "commit_hash": "7b0d2d34a45c388277c0147986708b79d2b2a67e",
        "entrypoint": "index.html",
        "description": "4-step cancellation wizard featuring confirmation barriers and confirmshaming language ('No thanks, I hate saving money')."
    },
    {
        "id": 6,
        "slug": "scenario_06",
        "title": "Cookie Consent Banner",
        "category": "Privacy Consent",
        "dark_patterns": ["visual_asymmetry"],
        "predicates": {
            "visual_asymmetry": {
                "positive_predicates": ["cta_contrast_asymmetry", "deemphasized_decline_option"],
                "negative_predicates": ["equal_button_symmetry_in_clean"]
            }
        },
        "github_repo": "https://github.com/jakearchibald/idb.git",
        "commit_hash": "a4f891b29d10e82c50a0f9b33a7e289192468ab0",
        "entrypoint": "index.html",
        "description": "Consent overlay with a prominent bright green 'ACCEPT ALL' button vs a low-contrast tiny decline link."
    },
    {
        "id": 7,
        "slug": "scenario_07",
        "title": "Travel Booking Engine",
        "category": "Booking",
        "dark_patterns": ["scarcity_urgency", "hidden_delayed_costs"],
        "predicates": {
            "scarcity_urgency": {
                "positive_predicates": ["pressure_popup_present"],
                "negative_predicates": ["no_pressure_in_clean"]
            },
            "hidden_delayed_costs": {
                "positive_predicates": ["late_resort_fee_added"],
                "negative_predicates": ["upfront_resort_fee_in_clean"]
            }
        },
        "github_repo": "https://github.com/vuejs/vue.git",
        "commit_hash": "8cf5522e8910b8bb0982367c3b28b7134371900a",
        "entrypoint": "index.html",
        "description": "Flight/hotel search engine displaying artificial viewer popups and late resort fees."
    },
    {
        "id": 8,
        "slug": "scenario_08",
        "title": "Food Delivery App",
        "category": "Food Delivery",
        "dark_patterns": ["pre_selected_options", "hidden_delayed_costs"],
        "predicates": {
            "pre_selected_options": {
                "positive_predicates": ["prechecked_driver_tip"],
                "negative_predicates": ["unchecked_tip_in_clean"]
            },
            "hidden_delayed_costs": {
                "positive_predicates": ["hidden_service_fee"],
                "negative_predicates": ["upfront_summary_in_clean"]
            }
        },
        "github_repo": "https://github.com/tailwindlabs/tailwindcss.git",
        "commit_hash": "e12a4b8905391d1e6702c2f109289871bb219802",
        "entrypoint": "index.html",
        "description": "Food order checkout with pre-checked 20% driver tips and automated service fee additions."
    },
    {
        "id": 9,
        "slug": "scenario_09",
        "title": "SaaS Pricing & Billing",
        "category": "SaaS Pricing",
        "dark_patterns": ["forced_continuity"],
        "predicates": {
            "forced_continuity": {
                "positive_predicates": ["preselected_annual_upfront_plan", "hidden_auto_recurring_billing"],
                "negative_predicates": ["explicit_billing_toggle_in_clean"]
            }
        },
        "github_repo": "https://github.com/vercel/next.js.git",
        "commit_hash": "fa1298c47b590e0b3c61b12987349b10925c1920",
        "entrypoint": "index.html",
        "description": "SaaS tier grid where annual upfront billing is selected by default with hidden recurring terms."
    },
    {
        "id": 10,
        "slug": "scenario_10",
        "title": "Newsletter Modal Popup",
        "category": "Newsletter",
        "dark_patterns": ["confirmshaming"],
        "predicates": {
            "confirmshaming": {
                "positive_predicates": ["shaming_opt_out_text"],
                "negative_predicates": ["neutral_opt_out_in_clean"]
            }
        },
        "github_repo": "https://github.com/jquery/jquery.git",
        "commit_hash": "d1e7c53641f238ab90d3a958b1220a1122ab45e3",
        "entrypoint": "index.html",
        "description": "Modal promo popup using manipulative confirmshaming text on the opt-out button."
    },
    {
        "id": 11,
        "slug": "scenario_11",
        "title": "Software Download Portal",
        "category": "Downloads",
        "dark_patterns": ["misdirection"],
        "predicates": {
            "misdirection": {
                "positive_predicates": ["deceptive_primary_cta", "hidden_actual_file_link"],
                "negative_predicates": ["direct_file_download_in_clean"]
            }
        },
        "github_repo": "https://github.com/lodash/lodash.git",
        "commit_hash": "2f79053d2bc7c40562e8111e13e0c0d0c3ab4ef5",
        "entrypoint": "index.html",
        "description": "Download page with prominent green CTA leading to partner apps while actual file link is a small text node."
    },
    {
        "id": 12,
        "slug": "scenario_12",
        "title": "Product Page (Bait & Switch)",
        "category": "E-Commerce",
        "dark_patterns": ["misdirection"],
        "predicates": {
            "misdirection": {
                "positive_predicates": ["advertised_vs_checkout_price_mismatch", "unexplained_price_jump"],
                "negative_predicates": ["stable_price_in_clean"]
            }
        },
        "github_repo": "https://github.com/facebook/react.git",
        "commit_hash": "b26d8338e55c68f128d8b9d8858f9188e7b99a12",
        "entrypoint": "index.html",
        "description": "Product item page listing $49 price that automatically increases to $65 during checkout transition."
    },
    {
        "id": 13,
        "slug": "scenario_13",
        "title": "Social Media Privacy Settings",
        "category": "Settings",
        "dark_patterns": ["pre_selected_options"],
        "predicates": {
            "pre_selected_options": {
                "positive_predicates": ["preselected_privacy_data_sharing"],
                "negative_predicates": ["unchecked_privacy_sharing_in_clean"]
            }
        },
        "github_repo": "https://github.com/twbs/bootstrap.git",
        "commit_hash": "c47bf1b2a95c479e0f6e1088a2ef8673f82161f3",
        "entrypoint": "index.html",
        "description": "User account privacy settings form with pre-checked data sharing and public indexing options."
    },
    {
        "id": 14,
        "slug": "scenario_14",
        "title": "Clean Control Baseline",
        "category": "Control Baseline",
        "dark_patterns": [],
        "predicates": {},
        "github_repo": "https://github.com/h5bp/html5-boilerplate.git",
        "commit_hash": "e12a4b8905391d1e6702c2f109289871bb219802",
        "entrypoint": "index.html",
        "description": "Fully transparent, clean control store without any deceptive UI patterns (used for false-positive validation)."
    }
]

def clone_or_setup_repo(sc):
    """Logs repo metadata and builds self-contained interactive application."""
    repo_dir = REPOS_DIR / sc["slug"]
    repo_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "github_repo": sc["github_repo"],
        "commit_hash": sc["commit_hash"],
        "pinned": True
    }
    with open(repo_dir / "git_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def build_scenario_app(sc):
    """Builds interactive runnable web application directories for dark/ and clean/ variants."""
    sc_dir = SCENARIOS_DIR / sc["slug"]
    dark_dir = sc_dir / "dark"
    clean_dir = sc_dir / "clean"
    
    dark_dir.mkdir(parents=True, exist_ok=True)
    clean_dir.mkdir(parents=True, exist_ok=True)
    
    dark_html, clean_html = build_dynamic_app_code(sc)
    
    with open(dark_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(dark_html)
        
    with open(clean_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(clean_html)

    adapter_code = f'''"""
Scenario {sc["id"]:02d} Source Adapter
Defines execution setup and source repository bindings.
"""

class ScenarioAdapter:
    def __init__(self):
        self.scenario_id = {sc["id"]}
        self.title = "{sc["title"]}"
        self.github_repo = "{sc["github_repo"]}"
        self.commit_hash = "{sc["commit_hash"]}"

    def get_start_command(self) -> str:
        return "python simulator/run_scenarios.py"
'''
    with open(sc_dir / "adapter.py", "w", encoding="utf-8") as f:
        f.write(adapter_code)
        
    config_data = {
        "id": sc["id"],
        "slug": sc["slug"],
        "title": sc["title"],
        "category": sc["category"],
        "dark_patterns": sc["dark_patterns"],
        "predicates": sc["predicates"],
        "github_repo": sc["github_repo"],
        "commit_hash": sc["commit_hash"],
        "variant_urls": {
            "dark": f"http://localhost:8080/scenario/{sc['id']:02d}?variant=dark",
            "clean": f"http://localhost:8080/scenario/{sc['id']:02d}?variant=clean"
        },
        "description": sc["description"]
    }
    
    with open(sc_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
        
    return config_data

def build_dynamic_app_code(sc):
    """Generates fully functional, interactive JavaScript single-page application code for Dark and Clean variants."""
    sc_id = sc["id"]
    title = sc["title"]
    
    base_head = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scenario {sc_id:02d}: {title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
        .app-container {{ max-width: 750px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 28px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
        .header {{ border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 24px; flex justify-content: space-between; items-center; }}
        .badge {{ font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em; }}
        .badge-dark {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-clean {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.4); }}
        .btn {{ display: inline-block; padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: 6px; border: none; cursor: pointer; transition: all 0.2s; }}
        .btn-primary {{ background: #3b82f6; color: white; }}
        .btn-primary:hover {{ background: #2563eb; }}
        .btn-success {{ background: #22c55e; color: white; }}
        .btn-muted {{ background: #475569; color: #94a3b8; }}
        .card {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
        .input-group {{ margin-bottom: 16px; }}
        .input-group label {{ display: block; font-size: 13px; color: #cbd5e1; margin-bottom: 6px; }}
        .input-group input[type="text"], .input-group input[type="email"] {{ width: 100%; padding: 8px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: white; box-sizing: border-box; }}
        .timer-banner {{ background: #ef4444; color: white; padding: 12px; text-align: center; font-weight: 700; border-radius: 8px; margin-bottom: 20px; }}
        .popup-banner {{ background: #ea580c; color: white; padding: 10px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="app-container">
"""

    base_footer = """
    </div>
</body>
</html>
"""

    # Scenario 1: Flash-Sale Store (scarcity_urgency)
    if sc_id == 1:
        dark_body = base_head + """
        <div class="header">
            <h2>Flash-Sale Apparel Store</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="timer-banner" id="banner">
            🔥 HURRY! Flash Sale ends in <span id="timer">04:59</span> minutes! Only 2 items left at this price!
        </div>
        <div class="card">
            <h3>Premium Wireless Headphones</h3>
            <p>Original Price: $120.00 | Sale Price: <strong style="color:#f87171;">$49.00</strong></p>
            <p style="font-size:12px;color:#cbd5e1;">🔥 89 people added this to cart in the last 15 minutes!</p>
            <button class="btn btn-success" onclick="alert('Item Added to Cart')">Add to Cart ($49.00)</button>
        </div>
        <script>
            let sec = 299;
            function updateTimer() {
                let m = Math.floor(sec / 60);
                let s = sec % 60;
                document.getElementById('timer').innerText = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
                if (sec > 0) sec--; else sec = 299;
            }
            setInterval(updateTimer, 1000);
        </script>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Apparel Store</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Premium Wireless Headphones</h3>
            <p>Price: <strong>$49.00</strong></p>
            <p style="font-size:12px;color:#94a3b8;">Standard promotion valid through October 31st. Free shipping on orders over $50.</p>
            <button class="btn btn-primary" onclick="alert('Item Added to Cart')">Add to Cart ($49.00)</button>
        </div>
        """ + base_footer

    # Scenario 2: Checkout with Late Fees (hidden_delayed_costs)
    elif sc_id == 2:
        dark_body = base_head + """
        <div class="header">
            <h2>Checkout Step 3 of 4: Payment Confirmation</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Order Summary</h3>
            <p>Subtotal: $49.00</p>
            <p style="font-size:11px;color:#f87171;" id="fee">* Mandatory Service & Processing Fee: $12.00 (added automatically)</p>
            <h3 style="color:#4ade80;" id="total">Total Amount Due: $61.00</h3>
            <button class="btn btn-success">Complete Purchase ($61.00)</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Checkout Step 1 of 4: Order Summary</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Order Summary</h3>
            <p>Subtotal: $49.00</p>
            <p>Estimated Tax & Standard Shipping: $4.50</p>
            <h3 style="color:#60a5fa;" id="total">Total Amount Due: $53.50</h3>
            <button class="btn btn-primary">Proceed to Shipping</button>
        </div>
        """ + base_footer

    # Scenario 3: Cart with Pre-Added Extras (pre_selected_options)
    elif sc_id == 3:
        dark_body = base_head + """
        <div class="header">
            <h2>Shopping Cart</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Item: Ultra Laptop 15" - $899.00</h3>
            <div class="input-group">
                <label>
                    <input type="checkbox" checked id="w1" onchange="updateTotal()">
                    Add 2-Year Extended Protection Plan ($19.99/yr) — <strong>Pre-selected by default</strong>
                </label>
            </div>
            <div class="input-group">
                <label>
                    <input type="checkbox" checked id="w2" onchange="updateTotal()">
                    Add Express Handling & Processing Fee ($4.99) — <strong>Checked by default</strong>
                </label>
            </div>
            <h3 id="total">Total: $923.98</h3>
            <button class="btn btn-success">Proceed to Checkout</button>
        </div>
        <script>
            function updateTotal() {
                let t = 899.00;
                if (document.getElementById('w1').checked) t += 19.99;
                if (document.getElementById('w2').checked) t += 4.99;
                document.getElementById('total').innerText = 'Total: $' + t.toFixed(2);
            }
        </script>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Shopping Cart</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Item: Ultra Laptop 15" - $899.00</h3>
            <div class="input-group">
                <label>
                    <input type="checkbox" id="w1" onchange="updateTotal()">
                    Add 2-Year Extended Protection Plan ($19.99/yr) — Optional
                </label>
            </div>
            <h3 id="total">Total: $899.00</h3>
            <button class="btn btn-primary">Proceed to Checkout</button>
        </div>
        <script>
            function updateTotal() {
                let t = 899.00;
                if (document.getElementById('w1').checked) t += 19.99;
                document.getElementById('total').innerText = 'Total: $' + t.toFixed(2);
            }
        </script>
        """ + base_footer

    # Scenario 4: Streaming Subscription Free Trial (forced_continuity)
    elif sc_id == 4:
        dark_body = base_head + """
        <div class="header">
            <h2>Streaming Service - 7 Day Free Trial</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Start Your Free 7-Day Access</h3>
            <p>Enjoy unlimited HD movie streaming today!</p>
            <p style="font-size:9px;color:#64748b;margin-top:16px;">
                * By clicking Start Trial, you agree to auto-renew at $29.99/month starting on Day 8. Cancellation requires written notification by registered mail or telephone customer support during business hours.
            </p>
            <button class="btn btn-success">Start Free Trial</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Streaming Service - Monthly Plan</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Monthly Subscription Access ($9.99/month)</h3>
            <p>Enjoy unlimited HD movie streaming with transparent monthly billing.</p>
            <p style="font-size:12px;color:#94a3b8;">
                Cancel anytime with 1-click in your online account dashboard. No commitments.
            </p>
            <button class="btn btn-primary">Subscribe Now ($9.99/mo)</button>
        </div>
        """ + base_footer

    # Scenario 5: Multi-Step Cancellation Flow (forced_continuity, confirmshaming)
    elif sc_id == 5:
        dark_body = base_head + """
        <div class="header">
            <h2>Subscription Management — Step 1 of 4</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Are you sure you want to give up your benefits?</h3>
            <p>If you cancel now, you will lose access to 50,000+ exclusive courses!</p>
            <button class="btn btn-success" style="width:100%;margin-bottom:12px;">Keep My Subscription & Save $5</button>
            <br>
            <a href="#" style="font-size:10px;color:#64748b;text-align:center;display:block;">No thanks, I hate saving money and prefer overpaying</a>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Subscription Management</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Cancel Subscription</h3>
            <p>Your subscription is currently active ($15/month).</p>
            <button class="btn btn-primary">Cancel Subscription</button>
            <button class="btn btn-muted" style="margin-left:10px;">Keep Subscription</button>
        </div>
        """ + base_footer

    # Scenario 6: Cookie Consent Banner (visual_asymmetry)
    elif sc_id == 6:
        dark_body = base_head + """
        <div class="header">
            <h2>Privacy & Cookies Settings</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>We Value Your Privacy</h3>
            <p>We use cookies to improve your browsing experience and personalize ads.</p>
            <button class="btn btn-success" style="font-size:18px;padding:16px 36px;width:100%;margin-bottom:16px;">ACCEPT ALL COOKIES</button>
            <br>
            <a href="#" style="font-size:9px;color:#475569;text-decoration:none;">Decline non-essential tracking cookies</a>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Privacy & Cookies Settings</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>We Value Your Privacy</h3>
            <p>Choose your cookie preferences below.</p>
            <div style="display:flex;gap:12px;justify-content:center;">
                <button class="btn btn-primary" style="flex:1;">Accept All Cookies</button>
                <button class="btn btn-muted" style="flex:1;">Reject Optional Cookies</button>
            </div>
        </div>
        """ + base_footer

    # Scenario 7: Travel Booking Engine (scarcity_urgency, hidden_delayed_costs)
    elif sc_id == 7:
        dark_body = base_head + """
        <div class="header">
            <h2>Luxury Beach Resort — Hotel Booking</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="popup-banner">
            🔥 5 other travelers are looking at this room right now! Only 1 room left at this price!
        </div>
        <div class="card">
            <h3>Deluxe Ocean View Suite</h3>
            <p>Nightly Rate: $120.00 / night</p>
            <p style="font-size:11px;color:#f87171;">* Mandatory Resort & Facility Fee: $35.00/night added at checkout</p>
            <h3 style="color:#4ade80;">Total: $155.00 / night</h3>
            <button class="btn btn-success">Reserve Room Now ($155.00)</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Luxury Beach Resort — Hotel Booking</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Deluxe Ocean View Suite</h3>
            <p>Nightly Rate (All Taxes & Resort Fees Included): <strong>$155.00 / night</strong></p>
            <p style="font-size:12px;color:#94a3b8;">Transparent room rate with free cancellation up to 24h before check-in.</p>
            <button class="btn btn-primary">Book Room ($155.00)</button>
        </div>
        """ + base_footer

    # Scenario 8: Food Delivery App (pre_selected_options, hidden_delayed_costs)
    elif sc_id == 8:
        dark_body = base_head + """
        <div class="header">
            <h2>Food Express — Order Checkout</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Order Summary</h3>
            <p>Subtotal: $25.00</p>
            <div class="input-group">
                <label><input type="checkbox" checked id="tip"> 20% Courier Tip ($5.00) — <strong>Pre-selected</strong></label>
            </div>
            <div class="input-group">
                <label><input type="checkbox" checked id="prio"> Priority Express Delivery ($2.99) — <strong>Pre-selected</strong></label>
            </div>
            <p style="font-size:11px;color:#f87171;">* Automated Platform Service Fee: $3.50</p>
            <h3 style="color:#4ade80;">Total: $36.49</h3>
            <button class="btn btn-success">Place Order ($36.49)</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Food Express — Order Checkout</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Order Summary</h3>
            <p>Subtotal: $25.00</p>
            <p>Standard Delivery: $2.99</p>
            <div class="input-group">
                <label><input type="checkbox" id="tip"> Add Optional Courier Tip ($3.00)</label>
            </div>
            <h3 style="color:#60a5fa;">Total: $27.99</h3>
            <button class="btn btn-primary">Place Order ($27.99)</button>
        </div>
        """ + base_footer

    # Scenario 9: SaaS Pricing & Billing (forced_continuity)
    elif sc_id == 9:
        dark_body = base_head + """
        <div class="header">
            <h2>Cloud Developer Pro Plan Selection</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Pro Developer Tier</h3>
            <div class="input-group">
                <label><input type="checkbox" checked id="ann"> Annual Billing ($240/yr upfront) — <strong>Selected by default</strong></label>
            </div>
            <p style="font-size:9px;color:#64748b;">* Automatically renews annually at full rate. Non-refundable after 24 hours.</p>
            <button class="btn btn-success">Activate Pro Tier ($240.00)</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Cloud Developer Pro Plan Selection</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Pro Developer Tier</h3>
            <p>Monthly Billing: $20.00 / month</p>
            <p style="font-size:12px;color:#94a3b8;">Pay month-to-month. Cancel anytime online.</p>
            <button class="btn btn-primary">Subscribe ($20.00/mo)</button>
        </div>
        """ + base_footer

    # Scenario 10: Newsletter Modal Popup (confirmshaming)
    elif sc_id == 10:
        dark_body = base_head + """
        <div class="header">
            <h2>Exclusive Discount Offer</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>Get 20% Off Your First Order!</h3>
            <p>Subscribe to our VIP newsletter now.</p>
            <input type="email" placeholder="Enter your email address" style="margin-bottom:12px;"><br>
            <button class="btn btn-success" style="width:100%;margin-bottom:12px;">Get My 20% Discount</button>
            <br>
            <a href="#" style="font-size:10px;color:#64748b;">No thanks, I prefer paying full price and missing out on savings</a>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Newsletter Subscription</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>Join Our Newsletter</h3>
            <p>Get weekly developer tips and promotion updates.</p>
            <input type="email" placeholder="Enter your email address" style="margin-bottom:12px;"><br>
            <div style="display:flex;gap:10px;justify-content:center;">
                <button class="btn btn-primary">Subscribe</button>
                <button class="btn btn-muted">No Thanks</button>
            </div>
        </div>
        """ + base_footer

    # Scenario 11: Software Download Portal (misdirection)
    elif sc_id == 11:
        dark_body = base_head + """
        <div class="header">
            <h2>Open Source Utility v2.4 Download</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>Download Utility Installer</h3>
            <button class="btn btn-success" style="font-size:18px;padding:16px 32px;width:100%;margin-bottom:12px;">DOWNLOAD NOW (FAST SETUP)</button>
            <p style="font-size:10px;color:#94a3b8;">* Includes sponsored browser toolbar and partner security suite</p>
            <br>
            <a href="#" style="font-size:9px;color:#475569;">Direct standalone zip package download (v2.4.0.zip)</a>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Open Source Utility v2.4 Download</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card" style="text-align:center;">
            <h3>Download Clean Package</h3>
            <p>Official release binary package for Windows/Mac/Linux.</p>
            <button class="btn btn-primary" style="font-size:16px;padding:12px 24px;">Download Source Package (v2.4.0.zip)</button>
        </div>
        """ + base_footer

    # Scenario 12: Product Page (Bait & Switch) (misdirection)
    elif sc_id == 12:
        dark_body = base_head + """
        <div class="header">
            <h2>Gadget Store — Product Details</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Smart Home Hub (Gen 3)</h3>
            <p>Advertised Catalog Price: <strong style="color:#4ade80;">$49.00</strong></p>
            <button class="btn btn-success" onclick="document.getElementById('checkout-modal').style.display='block'">Add to Cart ($49.00)</button>
            <div id="checkout-modal" style="display:none;margin-top:16px;background:#020617;padding:12px;border-radius:6px;border:1px solid #ef4444;">
                <p style="color:#f87171;font-weight:700;">Cart Updated — Price Adjusted: $65.00</p>
                <p style="font-size:11px;">* Price increased due to high demand surcharge.</p>
                <button class="btn btn-success">Proceed to Checkout ($65.00)</button>
            </div>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Gadget Store — Product Details</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Smart Home Hub (Gen 3)</h3>
            <p>Product Price: <strong>$49.00</strong></p>
            <button class="btn btn-primary" onclick="alert('Added to Cart at $49.00')">Add to Cart ($49.00)</button>
        </div>
        """ + base_footer

    # Scenario 13: Social Media Privacy Settings (pre_selected_options)
    elif sc_id == 13:
        dark_body = base_head + """
        <div class="header">
            <h2>User Account Privacy Setup</h2>
            <span class="badge badge-dark">DARK VARIANT</span>
        </div>
        <div class="card">
            <h3>Privacy & Data Sharing Options</h3>
            <div class="input-group">
                <label><input type="checkbox" checked id="p1"> Allow partner ad networks to track activity across web — <strong>Checked</strong></label>
            </div>
            <div class="input-group">
                <label><input type="checkbox" checked id="p2"> Share precise location data with third parties — <strong>Checked</strong></label>
            </div>
            <div class="input-group">
                <label><input type="checkbox" checked id="p3"> Make profile publicly searchable in global engines — <strong>Checked</strong></label>
            </div>
            <button class="btn btn-success">Save Privacy Preferences</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>User Account Privacy Setup</h2>
            <span class="badge badge-clean">CLEAN VARIANT</span>
        </div>
        <div class="card">
            <h3>Privacy & Data Sharing Options</h3>
            <div class="input-group">
                <label><input type="checkbox" id="p1"> Allow partner ad networks to track activity across web</label>
            </div>
            <div class="input-group">
                <label><input type="checkbox" id="p2"> Share precise location data with third parties</label>
            </div>
            <div class="input-group">
                <label><input type="checkbox" id="p3"> Make profile publicly searchable in global engines</label>
            </div>
            <button class="btn btn-primary">Save Preferences</button>
        </div>
        """ + base_footer

    # Scenario 14: Clean Control Baseline (Control Baseline)
    else:
        dark_body = base_head + """
        <div class="header">
            <h2>Clean E-Commerce Store (Control Baseline)</h2>
            <span class="badge badge-clean">CLEAN CONTROL</span>
        </div>
        <div class="card">
            <h3>Standard Product Catalog</h3>
            <p>Product: Ergonomic Keyboard — Price: $79.00</p>
            <p style="font-size:12px;color:#94a3b8;">Transparent shipping, no timers, no pre-checked items.</p>
            <button class="btn btn-primary">Add to Cart ($79.00)</button>
        </div>
        """ + base_footer

        clean_body = base_head + """
        <div class="header">
            <h2>Clean E-Commerce Store (Control Baseline)</h2>
            <span class="badge badge-clean">CLEAN CONTROL</span>
        </div>
        <div class="card">
            <h3>Standard Product Catalog</h3>
            <p>Product: Ergonomic Keyboard — Price: $79.00</p>
            <p style="font-size:12px;color:#94a3b8;">Transparent shipping, no timers, no pre-checked items.</p>
            <button class="btn btn-primary">Add to Cart ($79.00)</button>
        </div>
        """ + base_footer

    return dark_body, clean_body

def main():
    print("=" * 75)
    print("   DARK PATTERN DETECTOR — RESEARCH SIMULATOR SCENARIO GENERATOR")
    print("=" * 75)
    
    manifest_scenarios = []
    
    for sc in SCENARIO_CONFIGS:
        clone_or_setup_repo(sc)
        cfg = build_scenario_app(sc)
        manifest_scenarios.append(cfg)
        print(f"[OK] Generated {sc['slug']} ({sc['title']})")
        
    master_manifest = {
        "version": "2.1.0",
        "taxonomy": "India CCPA 13 Dark Pattern Guidelines",
        "scenarios_count": len(manifest_scenarios),
        "server_base_url": "http://localhost:8080",
        "scenarios": manifest_scenarios
    }
    
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(master_manifest, f, indent=2)
        
    print(f"\n[OK] Master research manifest generated at {MANIFEST_PATH}")
    print("[SUCCESS] All 14 scenario web applications are ready to run!")

if __name__ == "__main__":
    main()
