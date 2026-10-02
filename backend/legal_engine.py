"""
Legal & Regulatory Advisory Engine for Dark Pattern Detection
Provides non-speculative, jurisdiction-aware reference citations for educational
and advisory context. Explicitly isolates legal references from automated proof of illegality.
"""

from typing import Dict, Any, List

LEGAL_MAPPINGS: Dict[str, Dict[str, Any]] = {
    "scarcity_urgency": {
        "law_title": "Advisory: FTC §5 & UK CMA Deceptive Scarcity Guidelines",
        "jurisdictions": ["US (FTC)", "UK (CMA)", "EU (UCPD)"],
        "legal_citation": "15 U.S.C. § 45(a) / UCPD Annex I Item 5",
        "summary": "Artificial urgency or unverified stock scarcity claims are scrutinized under fair trade guidelines if representations are non-factual.",
        "severity": "MEDIUM",
        "consumer_tip": "Scarcity claims may be static or promotional. Verify stock or prices on independent comparison sources before purchasing."
    },
    "pre_selected_options": {
        "law_title": "Advisory: GDPR Art. 7 & EU UCPD Choice Guidelines",
        "jurisdictions": ["EU (GDPR / UCPD)", "UK", "US (FTC)"],
        "legal_citation": "GDPR Recital 32 / Planet49 C-673/17",
        "summary": "Pre-ticked checkboxes or default options are restricted in certain jurisdictions requiring explicit affirmative consent.",
        "severity": "HIGH",
        "consumer_tip": "Review default selected options, optional insurance, or newsletter checkmarks before confirming order."
    },
    "visual_asymmetry": {
        "law_title": "Advisory: EU Digital Services Act (DSA) Article 25",
        "jurisdictions": ["EU (DSA)", "US (FTC Guidelines)"],
        "legal_citation": "EU DSA Regulation 2022/2065 Art. 25(1)",
        "summary": "Obscuring or diminishing opt-out or decline choices is regulated under online choice architecture directives.",
        "severity": "HIGH",
        "consumer_tip": "Look closely for faint, low-contrast, or secondary links when declining popups or cookie banners."
    },
    "confirmshaming": {
        "law_title": "Advisory: FTC Deceptive Practices & EU Choice Guidance",
        "jurisdictions": ["US (FTC)", "EU (DSA)"],
        "legal_citation": "15 U.S.C. § 45 / DSA Art. 25",
        "summary": "Emotional guilt or manipulative opt-out phrasing is identified in consumer choice architecture research.",
        "severity": "MEDIUM",
        "consumer_tip": "Ignore guilt-inducing opt-out text ('No thanks, I hate saving money'). It is a marketing technique."
    },
    "hidden_delayed_costs": {
        "law_title": "Advisory: FTC Fee Rule & EU Price Indication Directive",
        "jurisdictions": ["US (FTC)", "EU", "UK"],
        "legal_citation": "16 CFR Part 464 (FTC Regulation) / Directive 98/6/EC",
        "summary": "Undisclosed mandatory charges or drip pricing revealed late in checkout are subject to fee transparency rules.",
        "severity": "CRITICAL",
        "consumer_tip": "Check itemized price breakdown before submitting payment to ensure no unrequested fees were added."
    },
    "forced_continuity": {
        "law_title": "Advisory: FTC Click-to-Cancel & Automatic Renewal Laws",
        "jurisdictions": ["US (FTC / CA ARL)", "EU (DSA)", "UK"],
        "legal_citation": "16 CFR Part 425 / Cal. Bus. & Prof. Code § 17600",
        "summary": "Auto-renewing subscriptions must provide clear terms and simple cancellation mechanisms under renewal laws.",
        "severity": "CRITICAL",
        "consumer_tip": "Set a reminder before trial expiration and check the provider's subscription cancellation policy."
    },
    "misdirection": {
        "law_title": "Advisory: EU DSA Art. 25 & FTC Deceptive UI Guidelines",
        "jurisdictions": ["EU (DSA)", "US (FTC)", "UK (CMA)"],
        "legal_citation": "DSA Art. 25(1)(a) / FTC Dot Com Disclosures",
        "summary": "Misleading visual cues or button label mismatches are evaluated under deceptive trade guidelines.",
        "severity": "HIGH",
        "consumer_tip": "Hover over links to verify destination URLs before clicking download or consent actions."
    }
}


def enrich_finding_with_legal_compliance(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches finding with non-speculative legal reference context."""
    category = finding.get("category", "")
    info = LEGAL_MAPPINGS.get(category, {
        "law_title": "Advisory: Fair Choice Architecture Guidelines",
        "jurisdictions": ["Global"],
        "legal_citation": "General Fair Trade Practices",
        "summary": "Potential non-neutral choice architecture pattern detected.",
        "severity": "MEDIUM",
        "consumer_tip": "Exercise caution and verify details before confirming transactions."
    })

    enriched = dict(finding)
    enriched["legal_info"] = info
    enriched["severity"] = info["severity"]
    return enriched


def calculate_risk_assessment(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates overall Dark Pattern Threat Assessment."""
    if not findings:
        return {
            "risk_score": 0,
            "risk_level": "LOW / CLEAN",
            "threat_color": "#16a34a",
            "summary": "No deceptive patterns detected. Interface exhibits standard choice architecture."
        }

    weight_map = {"CRITICAL": 30, "HIGH": 20, "MEDIUM": 10, "LOW": 5}
    total_points = 0

    for f in findings:
        cat = f.get("category", "")
        sev = LEGAL_MAPPINGS.get(cat, {}).get("severity", "MEDIUM")
        total_points += weight_map.get(sev, 10)

    risk_score = min(100, total_points)

    if risk_score >= 60:
        level = "HIGH RISK"
        color = "#dc2626"
    elif risk_score >= 35:
        level = "MODERATE RISK"
        color = "#ea580c"
    elif risk_score >= 15:
        level = "ELEVATED SIGNAL"
        color = "#d97706"
    else:
        level = "LOW SIGNAL"
        color = "#16a34a"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "threat_color": color,
        "total_violations": len(findings),
        "summary": f"Detected {len(findings)} potential pattern(s) resulting in an advisory risk score of {risk_score}/100."
    }
