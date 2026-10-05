// Popup Script for UPF Universal Pattern Finder
console.log('[UPF Detector] Popup script initialized');

let timerInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
  await checkBackendStatus();
  await updateUI();

  document.getElementById('sessionToggleBtn').addEventListener('click', toggleResearchSession);
  document.getElementById('inspectToggleBtn').addEventListener('click', toggleInspectMode);
  document.getElementById('scanBtn').addEventListener('click', scanPage);
  document.getElementById('clearBtn').addEventListener('click', clearHighlights);
  document.getElementById('autoScan').addEventListener('change', toggleAutoScan);

  if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
    chrome.runtime.onMessage.addListener((request) => {
      if (request.action === 'scanComplete' || request.action === 'traceUpdated') {
        updateUI();
      } else if (request.action === 'elementInspected') {
        renderInspectResult(request.data);
      }
    });
  }
});

async function checkBackendStatus() {
  try {
    const res = await fetch('http://localhost:8080/api/session/status', { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      setBackendUI('online', 'UPF Observatory 8080');
      return;
    }
  } catch (e) {}

  try {
    const res = await fetch('http://localhost:8000/health', { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      setBackendUI('online', 'Detector Backend 8000');
      return;
    }
  } catch (e) {}

  setBackendUI('offline');
}

function setBackendUI(status, labelText = '') {
  const dot = document.getElementById('backendDot');
  const label = document.getElementById('backendLabel');
  const badge = document.getElementById('modelBadge');

  if (dot) dot.className = `backend-dot ${status}`;
  if (label) {
    label.textContent = status === 'online' ? (labelText || 'Backend Connected') : 'Backend Offline';
  }
  if (badge) {
    badge.textContent = status === 'online' ? 'UPF Sensor v2' : 'Local Sensor';
  }
}

async function updateUI() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  const rawTitle = tab.title || tab.url || 'Active Tab';
  document.getElementById('pageTitle').textContent = rawTitle.length > 50 ? rawTitle.substring(0, 48) + '…' : rawTitle;

  chrome.storage.local.get(['isRecording', 'recordStartTime', 'recordedTrace', `findings_${tab.id}`, 'autoScan', 'latestPipelineStages', 'latestVerdict'], (result) => {
    const isRecording = result.isRecording === true;
    const recordedTrace = result.recordedTrace || [];
    const findings = result[`findings_${tab.id}`] || [];

    updateSessionUI(isRecording, result.recordStartTime, recordedTrace.length);

    document.getElementById('patternCount').textContent = findings.length;
    document.getElementById('autoScan').checked = result.autoScan !== false;

    if (result.latestPipelineStages) {
      renderPipelineGraph(result.latestPipelineStages, result.latestVerdict || 'PENDING');
    }

    if (findings.length > 0) {
      renderMultimodalFindings(findings);
    } else if (!isRecording) {
      renderEmptyState("No scan results yet. Click START RESEARCH SESSION or Quick Scan Page.");
    }
  });
}

function updateSessionUI(isRecording, recordStartTime, eventCount) {
  const toggleBtn = document.getElementById('sessionToggleBtn');
  const badge = document.getElementById('recordingBadge');
  const metrics = document.getElementById('sessionMetrics');
  const eventCountEl = document.getElementById('sessionEventCount');
  const graphCard = document.getElementById('pipelineGraphCard');

  if (isRecording) {
    toggleBtn.textContent = '⏹️ STOP RESEARCH SESSION';
    toggleBtn.className = 'btn btn-session-stop';
    badge.classList.remove('hidden');
    metrics.classList.remove('hidden');
    eventCountEl.textContent = `${eventCount} trace snapshot(s)`;
    if (graphCard) graphCard.classList.remove('hidden');

    startTimer(recordStartTime);
  } else {
    toggleBtn.textContent = '🔴 START RESEARCH SESSION';
    toggleBtn.className = 'btn btn-session-start';
    badge.classList.add('hidden');
    metrics.classList.add('hidden');
    stopTimer();
  }
}

function startTimer(startTime) {
  stopTimer();
  const timerEl = document.getElementById('sessionTimer');
  if (!startTime) startTime = Date.now();

  function tick() {
    const elapsedSec = Math.floor((Date.now() - startTime) / 1000);
    const m = String(Math.floor(elapsedSec / 60)).padStart(2, '0');
    const s = String(elapsedSec % 60).padStart(2, '0');
    if (timerEl) timerEl.textContent = `${m}:${s}`;
  }

  tick();
  timerInterval = setInterval(tick, 1000);
}

function stopTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = null;
}

async function toggleResearchSession() {
  chrome.storage.local.get(['isRecording', 'recordedTrace'], async (res) => {
    const currentlyRecording = res.isRecording === true;

    if (!currentlyRecording) {
      // START RESEARCH SESSION
      const startTime = Date.now();
      await chrome.storage.local.set({
        isRecording: true,
        recordStartTime: startTime,
        recordedTrace: []
      });

      // Trigger initial DOM scrape on active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.id) {
        chrome.tabs.sendMessage(tab.id, { action: 'scrapePage' }, (response) => {
          if (response && response.elements) {
            const initialTraceItem = {
              type: 'initial_snapshot',
              timestamp: new Date().toISOString(),
              url: response.url || tab.url,
              title: response.title || tab.title,
              elements: response.elements,
              texts: response.texts || []
            };
            chrome.storage.local.set({ recordedTrace: [initialTraceItem] });
          }
        });
      }

      updateUI();
    } else {
      // STOP RESEARCH SESSION & ANALYZE TRACE
      const trace = res.recordedTrace || [];
      await chrome.storage.local.set({ isRecording: false });

      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const payload = {
        session_id: `sess_free_${Date.now()}`,
        url: tab ? tab.url : 'https://example.com',
        title: tab ? tab.title : 'Free Browsing Research Session',
        trace: trace
      };

      renderAnalyzingState();

      try {
        let analyzeRes = null;
        try {
          const resp = await fetch('http://localhost:8080/api/session/analyze_trace', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          if (resp.ok) analyzeRes = await resp.json();
        } catch (e) {
          const resp = await fetch('http://localhost:8000/detect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ elements: trace.flatMap(t => t.elements || []) })
          });
          if (resp.ok) analyzeRes = await resp.json();
        }

        if (analyzeRes) {
          const verdict = analyzeRes.verdict || 'SUPPORTED';
          const stages = analyzeRes.pipeline_stages || [];

          await chrome.storage.local.set({
            latestPipelineStages: stages,
            latestVerdict: verdict
          });

          renderPipelineGraph(stages, verdict);

          if (analyzeRes.findings) {
            renderMultimodalFindings(analyzeRes.findings);
            renderUnresolvedQuestions(analyzeRes.unresolved_questions || []);
            if (tab && tab.id) {
              chrome.storage.local.set({ [`findings_${tab.id}`]: analyzeRes.findings });
            }
            document.getElementById('patternCount').textContent = analyzeRes.findings.length;
          }
        } else {
          renderEmptyState("Analysis complete. No dark patterns detected in trace.");
        }
      } catch (err) {
        alert('Failed to send trace to research server: ' + err.message);
      }

      updateUI();
    }
  });
}

function renderPipelineGraph(stages, verdict) {
  const card = document.getElementById('pipelineGraphCard');
  if (!card) return;

  card.classList.remove('hidden');

  const verdictBadge = document.getElementById('pipelineVerdictBadge');
  const verdictText = document.getElementById('pipelineVerdictText');

  const verdictClasses = {
    'SUPPORTED': 'badge-supported',
    'POTENTIAL': 'badge-potential',
    'NO EVIDENCE': 'badge-no-evidence',
    'INCONCLUSIVE': 'badge-inconclusive'
  };

  const badgeCls = verdictClasses[verdict] || 'badge-pending';
  if (verdictBadge) {
    verdictBadge.className = `verdict-badge ${badgeCls}`;
    verdictBadge.textContent = verdict;
  }
  if (verdictText) {
    verdictText.className = `result-badge ${badgeCls}`;
    verdictText.textContent = verdict;
  }

  // Render individual pipeline stage rows
  const stageMap = {
    1: 'stageRow_1',
    2: 'stageRow_2',
    3: 'stageRow_3',
    4: 'stageRow_4',
    6: 'stageRow_6',
    7: 'stageRow_7'
  };

  stages.forEach(st => {
    const rowId = stageMap[st.stage_id];
    if (rowId) {
      const row = document.getElementById(rowId);
      const detail = document.getElementById(`stageDetail_${st.stage_id}`);
      if (row) row.classList.add('completed');
      if (detail) detail.textContent = st.detail || 'Completed';
    }
  });

  // Activate parallel sub-stages (DOM DIFF, NETWORK, STORAGE)
  ['branch_dom', 'branch_net', 'branch_sto'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  });
}

function renderAnalyzingState() {
  const container = document.getElementById('findingsContainer');
  container.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚡</div>
      <p style="color:#0fb8f8;font-weight:bold;">Analyzing Interaction Pipeline…</p>
      <p class="sub-text">Executing stage-by-stage DOM, action & evidence fusion.</p>
    </div>
  `;
}

function renderMultimodalFindings(findings) {
  const container = document.getElementById('findingsContainer');
  container.innerHTML = '';

  if (!findings || findings.length === 0) {
    renderEmptyState();
    return;
  }

  const groupEl = document.createElement('div');
  groupEl.className = 'modality-group';
  groupEl.innerHTML = `<div class="modality-header">🔬 DETECTED PATTERNS (${findings.length})</div>`;

  findings.forEach(item => {
    const conf = Math.round((item.confidence || 0.90) * 100);
    const evText = item.evidence || '';

    const card = document.createElement('div');
    card.className = 'finding-card';
    card.innerHTML = `
      <div class="finding-top">
        <span class="finding-cat">${escapeHtml(item.category)}</span>
        <span class="finding-conf">${conf}% conf</span>
      </div>
      <div class="finding-evidence">"${escapeHtml(evText.substring(0, 100))}"</div>
      <div class="finding-reason">${escapeHtml(item.reason || '')}</div>
    `;
    groupEl.appendChild(card);
  });

  container.appendChild(groupEl);
}

function renderUnresolvedQuestions(questions) {
  const panel = document.getElementById('unresolvedPanel');
  const list = document.getElementById('unresolvedList');

  if (!questions || questions.length === 0) {
    panel.classList.add('hidden');
    return;
  }

  list.innerHTML = questions.map(q => `<li>${escapeHtml(q)}</li>`).join('');
  panel.classList.remove('hidden');
}

function renderEmptyState(msg) {
  const container = document.getElementById('findingsContainer');
  container.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">🛡️</div>
      <p>${msg || "No dark patterns detected."}</p>
    </div>
  `;
}

function scanPage() {
  chrome.runtime.sendMessage({ action: 'analyzePage' }, () => {
    setTimeout(updateUI, 1000);
  });
}

function clearHighlights() {
  chrome.runtime.sendMessage({ action: 'clearHighlights' }, () => {
    updateUI();
  });
}

function toggleAutoScan(e) {
  chrome.storage.local.set({ autoScan: e.target.checked });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function toggleInspectMode() {
  chrome.storage.local.get(['isInspectMode'], async (res) => {
    const nextState = !(res.isInspectMode === true);
    await chrome.storage.local.set({ isInspectMode: nextState });

    const btn = document.getElementById('inspectToggleBtn');
    if (btn) {
      if (nextState) {
        btn.textContent = '🎯 Inspect Element: ON';
        btn.style.background = '#2563eb';
        btn.style.color = '#ffffff';
        btn.style.borderColor = '#60a5fa';
      } else {
        btn.textContent = '🎯 Inspect Element: OFF';
        btn.style.background = '#0f172a';
        btn.style.color = '#60a5fa';
        btn.style.borderColor = '#3b82f6';
      }
    }

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.id) {
      chrome.tabs.sendMessage(tab.id, { action: 'toggleInspectMode', enabled: nextState }).catch(() => {});
    }
  });
}

function renderInspectResult(data) {
  const card = document.getElementById('inspectCard');
  if (!card) return;

  card.classList.remove('hidden');

  const badge = document.getElementById('inspectVerdictBadge');
  const txt = document.getElementById('inspectElementText');
  const cat = document.getElementById('inspectCategory');
  const reason = document.getElementById('inspectReason');
  const tip = document.getElementById('inspectTip');

  const isDark = data.is_dark_pattern === true || data.verdict === 'DARK_PATTERN';
  const conf = Math.round((data.confidence || 0) * 100);

  if (badge) {
    badge.textContent = isDark ? `⚠️ DARK PATTERN (${conf}%)` : `✅ CLEAN ELEMENT`;
    badge.style.background = isDark ? '#ef4444' : '#22c55e';
  }

  if (txt) {
    const rawText = data.evidence ? (Array.isArray(data.evidence) ? data.evidence[0] : data.evidence) : 'Target Element';
    txt.textContent = `Target: "${String(rawText).substring(0, 80)}"`;
  }

  if (cat) {
    cat.textContent = `Category: ${data.category || (isDark ? 'Deceptive Pattern' : 'Clean UI')}`;
  }

  if (reason) {
    reason.textContent = data.reason || (isDark ? 'Deceptive design pattern detected.' : 'Element is clean and transparent.');
  }

  if (tip) {
    const legal = data.legal_info || {};
    tip.innerHTML = `💡 <strong>Tip:</strong> ${legal.consumer_tip || (isDark ? 'Verify terms carefully.' : 'Element conforms to transparent UI guidelines.')}`;
  }
}