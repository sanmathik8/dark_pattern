"""
Multi-Modal Visual Heatmap & Annotation Engine
Annotates base64 screenshots with bounding boxes, category labels, and severity heatmaps.
"""

import io
import base64
import logging
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("dark-pattern-annotator")

def annotate_screenshot(screenshot_base64: str, findings: List[Dict[str, Any]]) -> str:
    """
    Draws bounding boxes and category labels on screenshot image.
    Returns annotated image as base64 string.
    """
    if not screenshot_base64 or not findings:
        return screenshot_base64

    # Clean base64 header
    prefix = ""
    if "," in screenshot_base64:
        prefix, screenshot_base64 = screenshot_base64.split(",", 1)

    try:
        img_bytes = base64.b64decode(screenshot_base64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)
    except Exception as e:
        log.error(f"Failed to load image for annotation: {e}")
        return screenshot_base64

    # Colors per category
    cat_colors = {
        "scarcity_urgency": "#ef4444",
        "pre_selected_options": "#f97316",
        "visual_asymmetry": "#eab308",
        "confirmshaming": "#a855f7",
        "hidden_delayed_costs": "#dc2626",
        "forced_continuity": "#b91c1c",
        "misdirection": "#3b82f6"
    }

    for item in findings:
        cat = item.get("category", "Dark Pattern")
        conf = MathRound(item.get("confidence", 0) * 100)
        color_hex = cat_colors.get(cat, "#ef4444")
        
        # Determine bounding rectangle
        rect = item.get("rect")
        bbox = item.get("bbox")

        box = None
        if bbox and len(bbox) == 4:
            box = bbox
        elif rect:
            box = [rect.get("x", 0), rect.get("y", 0), rect.get("x", 0) + rect.get("width", 0), rect.get("y", 0) + rect.get("height", 0)]

        if not box:
            continue

        x1, y1, x2, y2 = box
        # Draw bounding outline
        draw.rectangle([x1, y1, x2, y2], outline=color_hex, width=4)

        # Draw semi-transparent fill
        # Draw badge label
        label_text = f" {cat} ({conf}%) "
        label_bg = (239, 68, 68, 230)
        draw.rectangle([x1, max(0, y1 - 25), x1 + len(label_text) * 8 + 10, max(0, y1)], fill=label_bg)
        draw.text((x1 + 4, max(0, y1 - 22)), label_text, fill=(255, 255, 255))

    # Save output base64
    out_buffer = io.BytesIO()
    img.convert("RGB").save(out_buffer, format="PNG")
    b64_str = base64.b64encode(out_buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def MathRound(val):
    return int(round(val))
