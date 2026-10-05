// Background Service Worker for Dark Pattern Detector MV3
console.log('[Dark Pattern Detector] Stateful background service worker initialized');

const API_BASE_URL = 'http://localhost:8000';
const DETECT_ENDPOINT = '/detect';

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    enabled: true,
    autoScan: true,
    backendStatus: 'unknown',
    modelName: 'unknown'
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('chrome://')) {
    chrome.storage.local.get(['enabled', 'autoScan'], (result) => {
      if (result.enabled !== false && result.autoScan !== false) {
        analyzePage(tabId, tab);
      }
    });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'analyzePage':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) analyzePage(tabs[0].id, tabs[0]);
      });
      sendResponse({ success: true, message: 'Analysis started' });
      break;

    case 'pageMutated':
      if (sender.tab && sender.tab.id) {
        chrome.storage.local.get(['enabled', 'autoScan'], (result) => {
          if (result.enabled !== false && result.autoScan !== false) {
            analyzePage(sender.tab.id, sender.tab);
          }
        });
      }
      break;

    case 'clearHighlights':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.action.setBadgeText({ tabId: tabs[0].id, text: '' });
          chrome.tabs.sendMessage(tabs[0].id, { action: 'clearHighlights' }, () => {});
        }
      });
      sendResponse({ success: true });
      break;

    case 'inspectElement':
      (async () => {
        try {
          const resp = await fetch(`${API_BASE_URL}/api/inspect_element`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ element: request.element, threshold: 0.65 })
          });
          const inspectRes = await resp.json();
          sendResponse({ success: true, result: inspectRes });
        } catch (err) {
          sendResponse({ success: false, error: err.message });
        }
      })();
      return true;

    default:
      break;
  }
  return true;
});


async function analyzePage(tabId, tab) {
  try {
    console.log(`[Dark Pattern Detector] Analyzing stateful page: ${tab.url}`);
    chrome.storage.local.set({ [`scanStatus_${tabId}`]: 'scanning' });

    // 1. Get scraped page elements and state transition buffer from content script
    let pageData;
    try {
      pageData = await sendMessageToTab(tabId, { action: 'scrapePage' });
    } catch (e) {
      await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
      pageData = await sendMessageToTab(tabId, { action: 'scrapePage' });
    }

    if (!pageData || !pageData.elements) {
      chrome.storage.local.set({ [`scanStatus_${tabId}`]: 'done' });
      return;
    }

    // 2. Capture screenshot base64 for Vision Branch (Optional)
    let screenshotBase64 = "";
    try {
      screenshotBase64 = await chrome.tabs.captureVisibleTab(null, { format: 'png' });
    } catch (e) {
      console.log('[Dark Pattern Detector] Screenshot capture skipped:', e);
    }

    // 3. Post stateful payload to backend /detect endpoint
    const payload = {
      elements: pageData.elements,
      texts: pageData.texts || [],
      screenshot_base64: screenshotBase64,
      audio_base64: "",
      user_action: pageData.user_action || null,
      state_before: pageData.state_before || null,
      state_after: pageData.state_after || null,
      url: tab.url,
      threshold: 0.65
    };

    const response = await fetch(`${API_BASE_URL}${DETECT_ENDPOINT}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    const findingsCount = (data.findings || []).length;

    // Update Extension Icon Toolbar Badge
    if (findingsCount > 0) {
      chrome.action.setBadgeText({ tabId: tabId, text: String(findingsCount) });
      chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: '#dc2626' });
    } else {
      chrome.action.setBadgeText({ tabId: tabId, text: '✓' });
      chrome.action.setBadgeBackgroundColor({ tabId: tabId, color: '#16a34a' });
    }

    // 4. Update local storage & render highlights on overlay
    chrome.storage.local.set({
      backendStatus: 'online',
      modelName: data.model_type || 'stateful_flow',
      [`findings_${tabId}`]: data.findings || [],
      [`risk_${tabId}`]: data.risk_assessment || {},
      [`scanStatus_${tabId}`]: 'done'
    });

    await sendMessageToTab(tabId, {
      action: 'renderHighlights',
      findings: data.findings || []
    }).catch(() => {});

    chrome.runtime.sendMessage({ action: 'scanComplete', tabId }).catch(() => {});

  } catch (error) {
    console.error('[Dark Pattern Detector] Page analysis failed:', error);
    chrome.storage.local.set({
      backendStatus: 'offline',
      [`scanStatus_${tabId}`]: 'error'
    });
  }
}

function sendMessageToTab(tabId, message) {
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, message, (response) => {
      if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
      else resolve(response);
    });
  });
}