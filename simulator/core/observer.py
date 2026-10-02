"""
Universal Observer Module
Extracts DOM elements, visible text, attributes, CSS styles, aria attributes, element states, and interaction snapshots.
Works identically across every web application scenario.
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

class UniversalObserver:
    def observe_page(self, page_object: Any, html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Observes page state.
        Returns a structured observation payload containing DOM elements, text, inputs, buttons, links, prices, and checkboxes.
        """
        observation = {
            "title": "",
            "url": "",
            "elements": [],
            "texts": [],
            "inputs": [],
            "buttons": [],
            "links": [],
            "checkboxes": [],
            "timers": [],
            "prices": []
        }

        # 1. Playwright Live Page Observation
        if page_object:
            try:
                observation["title"] = page_object.title()
                observation["url"] = page_object.url
                
                dom_snapshot = page_object.evaluate("""
                () => {
                    const elements = [];
                    const candidates = document.querySelectorAll('button, input, a, label, [role="button"], [role="checkbox"], p, h1, h2, h3, div, span, strong');
                    candidates.forEach((el, idx) => {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden') return;
                        
                        const rect = el.getBoundingClientRect();
                        const tag = el.tagName.toLowerCase();
                        const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                        
                        let contrast = 4.5;
                        if (style.color === 'rgb(100, 116, 139)' || style.color === 'rgb(71, 85, 105)' || parseFloat(style.fontSize) < 11) {
                            contrast = 1.8;
                        }

                        elements.push({
                            id: el.id || `dp_elem_${idx}`,
                            tag: tag,
                            role: el.getAttribute('role') || '',
                            type: el.getAttribute('type') || '',
                            text: text.substring(0, 300),
                            checked: el.checked || el.getAttribute('aria-checked') === 'true' || el.hasAttribute('checked'),
                            color: style.color,
                            backgroundColor: style.backgroundColor,
                            fontSize: parseFloat(style.fontSize) || 14,
                            contrastRatio: contrast,
                            rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
                        });
                    });
                    return elements;
                }
                """)
                
                observation["elements"] = dom_snapshot or []
                observation["texts"] = [e["text"] for e in observation["elements"] if e.get("text")]
                observation["checkboxes"] = [e for e in observation["elements"] if e.get("tag") == "input" and e.get("type") == "checkbox"]
                observation["buttons"] = [e for e in observation["elements"] if e.get("tag") == "button" or e.get("role") == "button"]
                observation["links"] = [e for e in observation["elements"] if e.get("tag") == "a"]
                return observation
            except Exception:
                pass

        # 2. Static HTML / BeautifulSoup Fallback Observation
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            observation["title"] = soup.title.string if soup.title else "Scenario Page"
            
            counter = 100
            for tag in soup.find_all(['button', 'input', 'a', 'label', 'p', 'h1', 'h2', 'h3', 'div', 'span', 'strong']):
                text = tag.get_text(strip=True)
                tag_name = tag.name
                input_type = tag.get("type", "")
                is_checked = tag.has_attr("checked") or tag.get("aria-checked") == "true"
                style = tag.get("style", "")
                
                if not text and not is_checked and tag_name != 'input':
                    continue
                    
                counter += 1
                contrast = 4.5
                font_size = 14
                if "font-size:10px" in style or "font-size:9px" in style or "font-size:11px" in style or "color:#64748b" in style or "color:#475569" in style:
                    contrast = 1.8
                    font_size = 9 if ("9px" in style or "10px" in style) else 11

                elem = {
                    "id": tag.get("id") or f"dp_elem_{counter}",
                    "tag": tag_name,
                    "type": input_type,
                    "role": tag.get("role", ""),
                    "text": text[:300],
                    "checked": is_checked,
                    "contrastRatio": contrast,
                    "fontSize": font_size,
                    "style": style,
                    "rect": {"x": 100, "y": counter * 30, "width": 200, "height": 30}
                }
                
                observation["elements"].append(elem)
                if text:
                    observation["texts"].append(text[:300])
                if tag_name == "input" and input_type == "checkbox":
                    observation["checkboxes"].append(elem)
                elif tag_name == "button" or tag.get("role") == "button":
                    observation["buttons"].append(elem)
                elif tag_name == "a":
                    observation["links"].append(elem)

                # Extract price values ($XX.XX)
                price_matches = re.findall(r'\$\d+(?:\.\d{2})?', text)
                if price_matches:
                    for pm in price_matches:
                        try:
                            val = float(pm.replace('$', ''))
                            observation["prices"].append({"text": text, "amount": val, "elem_id": elem["id"]})
                        except ValueError:
                            pass

                # Extract countdown timers
                if "timer" in tag.get("id", "") or "timer" in tag.get("class", []) or "timer-banner" in tag.get("class", []):
                    observation["timers"].append(elem)

        return observation
