// Content script for Stateful Dark Pattern Detector MV3
// Strict Privacy & Stateful Web-Flow Snapshot Buffer

if (typeof window.DarkPatternDetectorInjected === 'undefined') {
  window.DarkPatternDetectorInjected = true;
  console.log('[Dark Pattern Detector] Stateful content script initialized');

  let elementCounter = 100;
  const elementMap = new Map();

  // Stateful Snapshot Buffer
  let lastStateSnapshot = null;
  let lastUserAction = null;

  function getOrCreateOverlayRoot() {
    let overlayRoot = document.getElementById('dark-pattern-overlay-root');
    if (!overlayRoot) {
      overlayRoot = document.createElement('div');
      overlayRoot.id = 'dark-pattern-overlay-root';
      overlayRoot.style.cssText = `
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        pointer-events: none !important;
        z-index: 2147483647 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
      `;
      (document.body || document.documentElement).appendChild(overlayRoot);
    }
    return overlayRoot;
  }

  function parseRgb(colorStr) {
    if (!colorStr || colorStr === 'transparent') return null;
    const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (match) {
      return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
    }
    return null;
  }

  function getResolvedBackgroundColor(element) {
    let curr = element;
    while (curr && curr !== document) {
      const style = window.getComputedStyle(curr);
      const bg = style.backgroundColor;
      const parsed = parseRgb(bg);
      if (parsed && (style.opacity === '1' || style.opacity === '')) {
        return parsed;
      }
      curr = curr.parentElement;
    }
    return [255, 255, 255];
  }

  function getLuminance([r, g, b]) {
    const a = [r, g, b].map(v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  }

  function calculateContrastRatio(fgRgb, bgRgb) {
    if (!fgRgb || !bgRgb) return 4.5;
    const l1 = getLuminance(fgRgb);
    const l2 = getLuminance(bgRgb);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return Math.round(((lighter + 0.05) / (darker + 0.05)) * 100) / 100;
  }

  class GeneralizedDOMScraper {
    constructor() {
      this.universalSelector = `
        button, input, a, label,
        [role="button"], [role="checkbox"], [role="option"], [role="radio"],
        p, h1, h2, h3, h4, span, section, div.banner, div.modal, li
      `;
    }

    scrapePage() {
      elementMap.clear();
      elementCounter = 100;

      const candidates = document.querySelectorAll(this.universalSelector);
      const scrapedElements = [];

      candidates.forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
          return;
        }

        const rect = el.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return;

        if (rect.bottom < 0 || rect.top > window.innerHeight || rect.right < 0 || rect.left > window.innerWidth) {
          return;
        }

        // STRICT PRIVACY P0 RULE
        // Never read input.value, textarea.value, or contenteditable user text!
        const tag = el.tagName.toLowerCase();
        const isEditable = el.isContentEditable || tag === 'textarea' || (tag === 'input' && !['button', 'submit', 'checkbox', 'radio', 'image'].includes(el.type));

        let safeText = "";
        if (isEditable) {
          safeText = el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.getAttribute('title') || "";
        } else {
          safeText = el.innerText || el.textContent || "";
        }

        safeText = safeText.replace(/\s+/g, ' ').trim();
        if (safeText.length > 300) safeText = safeText.substring(0, 300);

        const role = el.getAttribute('role') || "";
        const isInteractive = ['button', 'a', 'input', 'label'].includes(tag) || ['button', 'checkbox', 'radio', 'option'].includes(role);

        if (!safeText && !isInteractive) return;

        const dpId = `dp_elem_${++elementCounter}`;
        elementMap.set(dpId, el);

        const fgRgb = parseRgb(style.color) || [0, 0, 0];
        const bgRgb = getResolvedBackgroundColor(el);
        const contrast = calculateContrastRatio(fgRgb, bgRgb);

        let checked = false;
        if (tag === 'input' && (el.type === 'checkbox' || el.type === 'radio')) {
          checked = el.checked;
        } else if (el.getAttribute('aria-checked') === 'true') {
          checked = true;
        }

        scrapedElements.push({
          id: dpId,
          tag: tag,
          role: role,
          text: safeText,
          ariaLabel: el.getAttribute('aria-label') || null,
          placeholder: el.getAttribute('placeholder') || null,
          fontSize: parseFloat(style.fontSize) || 14,
          fontWeight: style.fontWeight,
          color: style.color,
          backgroundColor: style.backgroundColor,
          contrastRatio: contrast,
          checked: checked,
          hidden: false,
          rect: {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
          }
        });
      });

      return scrapedElements;
    }
  }

  const scraper = new GeneralizedDOMScraper();

  // ── Free-Browsing Research Session Trace Recorder ───────────────────────────
  function appendTraceSnapshot(actionObj) {
    if (typeof chrome === 'undefined' || !chrome.storage || !chrome.storage.local) return;
    chrome.storage.local.get(['isRecording', 'recordedTrace'], (res) => {
      if (res.isRecording === true) {
        const elements = scraper.scrapePage();
        const trace = res.recordedTrace || [];
        trace.push({
          type: actionObj ? actionObj.type : 'page_observation',
          timestamp: new Date().toISOString(),
          url: window.location.href,
          title: document.title,
          user_action: actionObj || lastUserAction,
          elements: elements,
          texts: elements.map(e => e.text)
        });
        chrome.storage.local.set({ recordedTrace: trace }, () => {
          if (chrome.runtime && chrome.runtime.sendMessage) {
            chrome.runtime.sendMessage({ action: 'traceUpdated', count: trace.length }).catch(() => {});
          }
        });
      }
    });
  }

  // Record initial page observation if recording session is active
  appendTraceSnapshot({ type: 'page_load', text: 'Page Loaded / Navigated', timestamp: new Date().toISOString() });

  // ── Element Inspector Mode ──────────────────────────────────────────────────
  let isInspectMode = false;
  let currentInspectHoverEl = null;

  function setInspectBanner(active) {
    let banner = document.getElementById('dp-inspect-banner');
    if (active) {
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'dp-inspect-banner';
        banner.style.cssText = `
          position: fixed !important;
          top: 12px !important;
          left: 50% !important;
          transform: translateX(-50%) !important;
          background: #2563eb !important;
          color: #ffffff !important;
          padding: 8px 18px !important;
          border-radius: 9999px !important;
          font-size: 12px !important;
          font-weight: 700 !important;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
          box-shadow: 0 4px 16px rgba(0,0,0,0.5) !important;
          z-index: 2147483647 !important;
          pointer-events: none !important;
          letter-spacing: 0.02em !important;
        `;
        banner.textContent = '🎯 ELEMENT INSPECTION MODE: Click ANY element on page to check if it\'s clean or a dark pattern';
        (document.body || document.documentElement).appendChild(banner);
      }
    } else {
      if (banner) banner.remove();
      if (currentInspectHoverEl) {
        currentInspectHoverEl.style.outline = '';
        currentInspectHoverEl = null;
      }
    }
  }

  document.addEventListener('mouseover', (e) => {
    if (!isInspectMode) return;
    if (currentInspectHoverEl && currentInspectHoverEl !== e.target) {
      currentInspectHoverEl.style.outline = '';
    }
    currentInspectHoverEl = e.target;
    if (currentInspectHoverEl && currentInspectHoverEl.id !== 'dp-inspect-banner') {
      currentInspectHoverEl.style.outline = '2px dashed #3b82f6';
    }
  }, { capture: true, passive: true });

  document.addEventListener('mouseout', (e) => {
    if (!isInspectMode) return;
    if (e.target && e.target === currentInspectHoverEl) {
      e.target.style.outline = '';
      currentInspectHoverEl = null;
    }
  }, { capture: true, passive: true });

  // ── Stateful Interaction Action Tracker ─────────────────────────────────────
  // Privacy P0 Enforced: Tracks clicked element metadata (ID, Tag, Safe Text), NEVER typed input values!
  document.addEventListener('click', (event) => {
    if (isInspectMode) {
      event.preventDefault();
      event.stopPropagation();

      const el = event.target;
      if (el) el.style.outline = '';

      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      const fgRgb = parseRgb(style.color) || [0,0,0];
      const bgRgb = getResolvedBackgroundColor(el);
      const contrast = calculateContrastRatio(fgRgb, bgRgb);
      const tag = el.tagName.toLowerCase();

      let safeText = "";
      const isEditable = el.isContentEditable || tag === 'textarea' || (tag === 'input' && !['button', 'submit', 'checkbox', 'radio', 'image'].includes(el.type));
      if (isEditable) {
        safeText = el.getAttribute('placeholder') || el.getAttribute('aria-label') || "";
      } else {
        safeText = el.innerText || el.textContent || el.value || "";
      }
      safeText = safeText.replace(/\s+/g, ' ').trim().substring(0, 300);

      const inspectItem = {
        id: el.id || `dp_inspect_${Date.now()}`,
        tag: tag,
        role: el.getAttribute('role') || "",
        text: safeText,
        ariaLabel: el.getAttribute('aria-label') || null,
        placeholder: el.getAttribute('placeholder') || null,
        fontSize: parseFloat(style.fontSize) || 14,
        color: style.color,
        contrastRatio: contrast,
        checked: el.checked || el.getAttribute('aria-checked') === 'true',
        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
      };

      chrome.runtime.sendMessage({ action: 'inspectElement', element: inspectItem }, (res) => {
        if (res && res.success && res.result) {
          const resultData = res.result;
          renderSingleInspectHighlight(el, resultData);
          if (chrome.runtime && chrome.runtime.sendMessage) {
            chrome.runtime.sendMessage({ action: 'elementInspected', data: resultData }).catch(() => {});
          }
        }
      });
      return false;
    }

    let target = event.target;
    while (target && target !== document.body) {
      const tag = target.tagName ? target.tagName.toLowerCase() : "";
      if (['button', 'a', 'input', 'label'].includes(tag) || target.getAttribute('role')) {
        const isEditableInput = tag === 'textarea' || (tag === 'input' && !['button', 'submit', 'checkbox', 'radio', 'image'].includes(target.type)) || target.isContentEditable;
        let safeActionText = "";
        if (isEditableInput) {
          safeActionText = target.getAttribute('placeholder') || target.getAttribute('aria-label') || tag;
        } else {
          safeActionText = target.innerText || target.value || target.getAttribute('aria-label') || tag;
        }
        safeActionText = safeActionText.replace(/\s+/g, ' ').trim().substring(0, 100);

        lastUserAction = {
          type: 'click',
          target_id: target.id || 'dp_elem_click',
          text: safeActionText,
          timestamp: new Date().toISOString()
        };
        appendTraceSnapshot(lastUserAction);
        break;
      }
      target = target.parentElement;
    }
  }, { capture: true, passive: false });

  // ── Overlay Rendering ───────────────────────────────────────────────────────
  let activeHighlights = [];

  function clearOverlay() {
    const root = getOrCreateOverlayRoot();
    root.innerHTML = '';
    activeHighlights = [];
  }

  function renderHighlightsOnOverlay(findings) {
    clearOverlay();
    const root = getOrCreateOverlayRoot();

    findings.forEach(finding => {
      const elemId = finding.element_id;
      let targetEl = elemId ? elementMap.get(elemId) : null;

      let rect = targetEl ? targetEl.getBoundingClientRect() : finding.rect;
      if (!rect) return;

      const category = finding.category || "Dark Pattern";
      const confidence = Math.round((finding.confidence || 0) * 100);
      const legal = finding.legal_info || {};

      const highlightBox = document.createElement('div');
      highlightBox.className = 'dp-overlay-highlight';
      highlightBox.style.cssText = `
        position: absolute !important;
        top: ${rect.top + window.scrollY}px !important;
        left: ${rect.left + window.scrollX}px !important;
        width: ${rect.width}px !important;
        height: ${rect.height}px !important;
        border: 2px solid #ef4444 !important;
        box-shadow: 0 0 8px rgba(239,68,68,0.5) !important;
        border-radius: 3px !important;
        pointer-events: none !important;
        box-sizing: border-box !important;
        transition: all 0.2s ease !important;
      `;

      const badge = document.createElement('div');
      badge.className = 'dp-overlay-badge';
      badge.textContent = `⚠️ ${category} · ${confidence}%`;
      badge.style.cssText = `
        position: absolute !important;
        top: -24px !important;
        left: 0 !important;
        background: #ef4444 !important;
        color: #ffffff !important;
        padding: 3px 8px !important;
        border-radius: 4px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
        white-space: nowrap !important;
        pointer-events: auto !important;
        cursor: pointer !important;
      `;

      const tooltip = document.createElement('div');
      tooltip.style.cssText = `
        display: none;
        position: absolute;
        top: 24px;
        left: 0;
        width: 270px;
        background: #1e293b;
        color: #f8fafc;
        padding: 10px;
        border-radius: 6px;
        font-size: 11px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        border: 1px solid #475569;
        z-index: 2147483647;
      `;
      
      const transitionText = finding.state_transition ? `<strong>State Transition:</strong> ${JSON.stringify(finding.state_transition)}<br>` : '';

      tooltip.innerHTML = `
        <div style="font-weight:bold;color:#f87171;margin-bottom:4px;">⚖️ ${legal.law_title || 'Consumer Protection Law'}</div>
        <div style="font-size:10px;color:#94a3b8;margin-bottom:6px;">Citation: ${legal.legal_citation || 'N/A'}</div>
        <div style="color:#e2e8f0;margin-bottom:6px;">${finding.reason || ''}</div>
        <div style="font-size:10px;color:#cbd5e1;margin-bottom:6px;">${transitionText}</div>
        <div style="background:#0f172a;padding:6px;border-radius:4px;color:#60a5fa;font-size:10px;">💡 <strong>Tip:</strong> ${legal.consumer_tip || 'Verify terms carefully.'}</div>
      `;

      badge.appendChild(tooltip);

      badge.addEventListener('mouseenter', () => tooltip.style.display = 'block');
      badge.addEventListener('mouseleave', () => tooltip.style.display = 'none');

      highlightBox.appendChild(badge);
      root.appendChild(highlightBox);

      activeHighlights.push({
        elementId: elemId,
        targetEl: targetEl,
        boxEl: highlightBox
      });
    });
  }

  function updateOverlayPositions() {
    activeHighlights.forEach(item => {
      if (item.targetEl && item.boxEl) {
        const rect = item.targetEl.getBoundingClientRect();
        item.boxEl.style.top = `${rect.top + window.scrollY}px`;
        item.boxEl.style.left = `${rect.left + window.scrollX}px`;
        item.boxEl.style.width = `${rect.width}px`;
        item.boxEl.style.height = `${rect.height}px`;
      }
    });
  }

  window.addEventListener('scroll', updateOverlayPositions, { passive: true });
  window.addEventListener('resize', updateOverlayPositions, { passive: true });

  let mutationTimeout = null;
  const observer = new MutationObserver(() => {
    if (mutationTimeout) clearTimeout(mutationTimeout);
    mutationTimeout = setTimeout(() => {
      if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
        chrome.runtime.sendMessage({ action: 'pageMutated' }).catch(() => {});
      }
    }, 2000);
  });

  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true
  });

  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      switch (request.action) {
        case 'scrapePage':
        case 'getPageText':
          const elements = scraper.scrapePage();
          const currentSnapshot = {
            url: window.location.href,
            title: document.title,
            elements: elements,
            timestamp: new Date().toISOString()
          };

          const stateBefore = lastStateSnapshot;
          lastStateSnapshot = currentSnapshot;

          sendResponse({
            success: true,
            elements: elements,
            texts: elements.map(e => e.text),
            user_action: lastUserAction,
            state_before: stateBefore,
            state_after: currentSnapshot,
            url: window.location.href,
            title: document.title
          });
          break;

        case 'renderHighlights':
          renderHighlightsOnOverlay(request.findings || []);
          sendResponse({ success: true, count: (request.findings || []).length });
          break;

        case 'clearHighlights':
          clearOverlay();
          sendResponse({ success: true });
          break;

        case 'toggleInspectMode':
          isInspectMode = request.enabled === true;
          setInspectBanner(isInspectMode);
          sendResponse({ success: true, isInspectMode: isInspectMode });
          break;

        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
      return true;
    });
  }

  function renderSingleInspectHighlight(targetEl, resultData) {
    const root = getOrCreateOverlayRoot();
    const rect = targetEl.getBoundingClientRect();
    if (!rect) return;

    const isDark = resultData.is_dark_pattern === true || resultData.verdict === 'DARK_PATTERN';
    const confidence = Math.round((resultData.confidence || 0) * 100);
    const category = resultData.category || (isDark ? "Dark Pattern" : "Clean Element");
    const color = isDark ? "#ef4444" : "#22c55e";

    const highlightBox = document.createElement('div');
    highlightBox.className = 'dp-overlay-highlight';
    highlightBox.style.cssText = `
      position: absolute !important;
      top: ${rect.top + window.scrollY}px !important;
      left: ${rect.left + window.scrollX}px !important;
      width: ${rect.width}px !important;
      height: ${rect.height}px !important;
      border: 2px solid ${color} !important;
      box-shadow: 0 0 10px ${color}80 !important;
      border-radius: 4px !important;
      pointer-events: none !important;
      z-index: 2147483647 !important;
      transition: all 0.2s ease !important;
    `;

    const badge = document.createElement('div');
    badge.className = 'dp-overlay-badge';
    badge.textContent = isDark ? `⚠️ ${category} · ${confidence}%` : `✅ CLEAN ELEMENT · 0% Dark Pattern`;
    badge.style.cssText = `
      position: absolute !important;
      top: -26px !important;
      left: 0 !important;
      background: ${color} !important;
      color: #ffffff !important;
      padding: 4px 10px !important;
      border-radius: 4px !important;
      font-size: 11px !important;
      font-weight: 700 !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
      white-space: nowrap !important;
      pointer-events: auto !important;
      cursor: pointer !important;
    `;

    highlightBox.appendChild(badge);
    root.appendChild(highlightBox);
  }
}