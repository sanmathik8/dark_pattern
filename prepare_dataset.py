"""
Prepare Multi-Label Dataset for 7 Dark Pattern Categories:
1. scarcity_urgency
2. pre_selected_options
3. visual_asymmetry
4. confirmshaming
5. hidden_delayed_costs
6. forced_continuity
7. misdirection
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_DATASET_PATH = BASE_DIR / "dataset.csv"
OUTPUT_PATH = BASE_DIR / "dark_patterns_multi_label.csv"

# Load base dataset
df = pd.read_csv(RAW_DATASET_PATH)
df['text'] = df['text'].fillna("").astype(str).str.strip()

# Initialize 7 category columns with 0
categories = [
    'scarcity_urgency',
    'pre_selected_options',
    'visual_asymmetry',
    'confirmshaming',
    'hidden_delayed_costs',
    'forced_continuity',
    'misdirection'
]

for cat in categories:
    df[cat] = 0

# Base category mapping
for idx, row in df.iterrows():
    cat_name = str(row.get('Pattern Category', ''))
    text = row['text'].lower()

    if cat_name in ['Scarcity', 'Urgency', 'Social Proof']:
        df.at[idx, 'scarcity_urgency'] = 1
    elif cat_name == 'Misdirection':
        df.at[idx, 'misdirection'] = 1
        if any(phrase in text for phrase in ['no thanks', 'i don\'t want', 'i hate', 'no, i prefer']):
            df.at[idx, 'confirmshaming'] = 1
    elif cat_name == 'Sneaking':
        df.at[idx, 'hidden_delayed_costs'] = 1
    elif cat_name in ['Obstruction', 'Forced Action']:
        df.at[idx, 'forced_continuity'] = 1

# Supplement with specific multi-label examples for underrepresented categories
additional_samples = [
    # Pre-selected options
    {"text": "Add 2-year extended warranty for $19.99 (Pre-selected)", "scarcity_urgency": 0, "pre_selected_options": 1, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},
    {"text": "Include optional travel protection insurance in your order", "scarcity_urgency": 0, "pre_selected_options": 1, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},
    {"text": "Yes, automatically renew my subscription every year", "scarcity_urgency": 0, "pre_selected_options": 1, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 1, "misdirection": 0},
    {"text": "Pre-checked: Subscribe to partner offer newsletters and promotions", "scarcity_urgency": 0, "pre_selected_options": 1, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},
    {"text": "Checked by default: Add express processing fee ($4.99)", "scarcity_urgency": 0, "pre_selected_options": 1, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},

    # Visual asymmetry
    {"text": "ACCEPT ALL COOKIES (Bright green large button) vs Reject non-essential (tiny gray link)", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 1, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},
    {"text": "Prominent glowing 'Upgrade Now' button alongside faded gray 'Maybe Later'", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 1, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 0},
    {"text": "Giant 'Continue to Checkout' button vs low contrast invisible cancel text", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 1, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},
    
    # Confirmshaming
    {"text": "No thanks, I prefer paying full price", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 1, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},
    {"text": "No thanks, I don't care about security", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 1, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},
    {"text": "No, I'd rather miss out on exclusive discounts", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 1, "hidden_delayed_costs": 0, "forced_continuity": 0, "misdirection": 1},

    # Hidden / Delayed Costs
    {"text": "*A service fee of $5.99 will be added at the final payment step", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},
    {"text": "Mandatory resort fee of $35/night added during checkout", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},
    {"text": "Price excludes handling fees and delivery surcharge", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 0, "misdirection": 0},

    # Forced Continuity
    {"text": "Start 7-day free trial. Automatically converts to $29.99/mo subscription. Call phone number to cancel.", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 1, "misdirection": 0},
    {"text": "Membership auto-renews annually. Cancellation requires written mail 30 days prior.", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 0, "forced_continuity": 1, "misdirection": 0},
    {"text": "Enter credit card to unlock free trial. Automatic billing begins after 3 days.", "scarcity_urgency": 0, "pre_selected_options": 0, "visual_asymmetry": 0, "confirmshaming": 0, "hidden_delayed_costs": 1, "forced_continuity": 1, "misdirection": 0},
]

add_df = pd.DataFrame(additional_samples)
final_df = pd.concat([df[['text'] + categories], add_df], ignore_index=True)

# Drop any blank texts
final_df = final_df[final_df['text'].str.len() > 0].reset_index(drop=True)

final_df.to_csv(OUTPUT_PATH, index=False)
print(f"Successfully generated {OUTPUT_PATH} with {len(final_df)} samples!")
print("\nCategory distribution:")
for cat in categories:
    print(f"  {cat}: {final_df[cat].sum()}")
