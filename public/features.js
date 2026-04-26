/* ═══════════════════════════════════════════════════════════════════
   features.js — opt-in feature bundles layered on top of app.js.

   #3  Concept-level analytics  →  window.recordConceptResults / renderConceptPanel
   #4  Flag & bookmark system   →  window.toggleFlag / renderFlagControl / loadFlags
   #6  Pacing indicator         →  window.updatePacing
   #9  Onboarding               →  window.maybeShowOnboarding / startDiagnostic
   #10 Polish (icons + prune)   →  window.icon / window.pruneHistory

   Loaded BEFORE app.js so app.js can call these helpers.
   ═══════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─────────── Shared DB helpers ─────────── */
  async function dbGet(key) {
    try { const r = await fetch('/api/db/' + key); if (!r.ok) return null; return (await r.json()).value; } catch { return null; }
  }
  async function dbSet(key, value) {
    try {
      await fetch('/api/db/' + key, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      });
    } catch {}
  }

  function escapeText(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
  }

  /* ═══════════════════════════════════════════════════════════════════
     #10 — Inline SVG icon helper (Material Symbols, currentColor)
     ═══════════════════════════════════════════════════════════════════ */
  const ICONS = {
    timer:    '<path d="M9 1h6v2H9V1zm10.05 4.36l1.41-1.41-1.42-1.42-1.4 1.41A9 9 0 1 0 21 13a8.96 8.96 0 0 0-1.95-7.64zM12 21a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM11 8h2v6h-2V8z"/>',
    book:     '<path d="M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z"/>',
    folder:   '<path d="M10 4H4c-1.11 0-2 .89-2 2v12a2 2 0 0 0 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>',
    brain:    '<path d="M13 3a3 3 0 0 0-3 3v.18A3 3 0 0 0 8.5 9 3 3 0 0 0 7 11.78V12a3 3 0 0 0 1.5 2.6V15a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-.18A3 3 0 0 0 17 12a3 3 0 0 0-1.5-2.6V9a3 3 0 0 0-1.5-2.6V6a3 3 0 0 0-1-2.83V3z"/>',
    sparkle:  '<path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5L12 2zm7 9l.75 2.25L22 14l-2.25.75L19 17l-.75-2.25L16 14l2.25-.75L19 11zm-13 1l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z"/>',
    home:     '<path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>',
    settings: '<path d="M19.14 12.94c.04-.3.06-.61.06-.94s-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41L9.25 5.35c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 0 1 8.4 12c0-1.99 1.61-3.6 3.6-3.6s3.6 1.61 3.6 3.6-1.61 3.6-3.6 3.6z"/>',
    star:     '<path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>',
    starOutline: '<path d="m12 15.4-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4zM22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24z"/>',
    play:     '<path d="M8 5v14l11-7z"/>',
    target:   '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-13a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>',
    chart:    '<path d="M3 13h2v8H3v-8zm4-5h2v13H7V8zm4-5h2v18h-2V3zm4 8h2v10h-2V11zm4 4h2v6h-2v-6z"/>',
    check:    '<path d="m9 16.17-4.17-4.17L3.41 13.41 9 19l12-12-1.41-1.41z"/>',
    flag:     '<path d="M14.4 6 14 4H5v17h2v-7h5.6l.4 2h7V6z"/>',
    flagOutline: '<path d="M12.36 6 12.76 8H18v6h-3.36l-.4-2H7V6h5.36zM14 4H5v17h2v-7h5.6l.4 2h7V6h-5.6L14 4z"/>',
    sun:      '<path d="M6.76 4.84l-1.8-1.79L3.55 4.46l1.79 1.8 1.42-1.42zM4 10.5H1v2h3v-2zm9-9.95h-2V3.5h2V.55zm7.45 3.91-1.41-1.41-1.79 1.79 1.41 1.41 1.79-1.79zm-3.21 13.7 1.79 1.8 1.41-1.41-1.8-1.79-1.4 1.4zM20 10.5v2h3v-2h-3zm-8-5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13zm-1 16.95h2V19.5h-2v2.95zm-7.45-3.91 1.41 1.41 1.79-1.8-1.41-1.41-1.79 1.8z"/>',
    moon:     '<path d="M9.5 2c-1.82 0-3.53.5-5 1.35 2.99 1.73 5 4.95 5 8.65s-2.01 6.92-5 8.65C5.97 21.5 7.68 22 9.5 22c5.52 0 10-4.48 10-10S15.02 2 9.5 2z"/>'
  };

  function icon(name, opts) {
    const path = ICONS[name];
    if (!path) return '';
    const size = (opts && opts.size) || 18;
    const cls  = 'icon' + ((opts && opts.cls) ? ' ' + opts.cls : '');
    return '<svg class="' + cls + '" width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' + path + '</svg>';
  }
  window.icon = icon;

  /* ═══════════════════════════════════════════════════════════════════
     #4 — Flag / bookmark system
     ═══════════════════════════════════════════════════════════════════ */
  let flagsCache = null;

  async function loadFlags() {
    flagsCache = (await dbGet('pca:flags')) || [];
    return flagsCache;
  }

  function isFlagged(id) {
    if (!flagsCache) return false;
    return flagsCache.indexOf(id) !== -1;
  }

  async function toggleFlag(id) {
    if (!flagsCache) await loadFlags();
    const i = flagsCache.indexOf(id);
    if (i === -1) flagsCache.push(id); else flagsCache.splice(i, 1);
    await dbSet('pca:flags', flagsCache);
    // Refresh visual state on the active question card if present
    const btn = document.getElementById('flag-btn');
    if (btn) renderFlagControl(id, btn);
    if (typeof window.showToast === 'function') {
      window.showToast(i === -1 ? 'Question flagged for review' : 'Flag removed');
    }
    return isFlagged(id);
  }

  function renderFlagControl(id, btn) {
    if (!btn) return;
    const flagged = isFlagged(id);
    btn.innerHTML = icon(flagged ? 'flag' : 'flagOutline', { size: 16 }) + (flagged ? ' Flagged' : ' Flag');
    btn.classList.toggle('is-flagged', flagged);
    btn.setAttribute('aria-pressed', flagged ? 'true' : 'false');
    btn.title = flagged ? 'Remove flag' : 'Flag this question for review';
  }

  async function startFlaggedSession() {
    const flagged = (await loadFlags()) || [];
    if (flagged.length === 0) {
      if (window.showToast) window.showToast('No flagged questions yet — tap the flag icon during a session');
      return;
    }
    const seed  = (await dbGet('pca:seed-questions')) || [];
    const extra = (await dbGet('pca:ai-questions')) || [];
    const pool  = seed.concat(extra);
    const set   = new Set(flagged);
    const qs    = pool.filter(q => set.has(q.id));
    if (qs.length === 0) {
      if (window.showToast) window.showToast('Flagged questions no longer exist in the pool');
      return;
    }
    if (window.state) {
      window.state.mode = 'flagged';
      window.state.questions = qs;
    }
    if (typeof window.initExamUI === 'function') window.initExamUI();
  }

  window.loadFlags = loadFlags;
  window.isFlagged = isFlagged;
  window.toggleFlag = toggleFlag;
  window.renderFlagControl = renderFlagControl;
  window.startFlaggedSession = startFlaggedSession;
  // Expose the in-memory flag cache (read-only) so the Review-Later panel
  // can compute which questions in the active session are flagged without
  // hitting storage on every render.
  window.getFlagsCache = function () { return flagsCache ? flagsCache.slice() : []; };

  /* ═══════════════════════════════════════════════════════════════════
     #3 — Concept-level analytics
     pca:concept-mastery shape: { "concept": { total, correct, lastSeen } }
     ═══════════════════════════════════════════════════════════════════ */
  async function recordConceptResults(questions, answers) {
    const m = (await dbGet('pca:concept-mastery')) || {};
    const now = Date.now();
    questions.forEach((q, i) => {
      const concepts = Array.isArray(q.concepts) ? q.concepts : [];
      if (concepts.length === 0) return;
      const correct = answers[i] === q.answer;
      concepts.forEach(c => {
        if (!c) return;
        const key = String(c).trim();
        if (!key) return;
        if (!m[key]) m[key] = { total: 0, correct: 0, lastSeen: now };
        m[key].total++;
        if (correct) m[key].correct++;
        m[key].lastSeen = now;
      });
    });
    await dbSet('pca:concept-mastery', m);
    return m;
  }

  async function renderConceptPanel(targetId) {
    const el = document.getElementById(targetId);
    if (!el) return;
    const m = (await dbGet('pca:concept-mastery')) || {};
    const ranked = Object.entries(m)
      .filter(([_, d]) => d && d.total >= 2)
      .map(([name, d]) => ({ name, total: d.total, correct: d.correct, pct: Math.round((d.correct / d.total) * 100) }))
      .sort((a, b) => a.pct - b.pct)
      .slice(0, 5);

    if (ranked.length === 0) {
      el.innerHTML = '<p class="concept-empty">Concept-level data appears here once AI-generated questions tag what they test.</p>';
      return;
    }

    const rows = ranked.map(c => {
      const cls = c.pct < 50 ? 'red' : c.pct < 75 ? 'yellow' : 'green';
      return '<li class="concept-row ' + cls + '">'
           +   '<div class="concept-name">' + escapeText(c.name) + '</div>'
           +   '<div class="concept-meta"><span class="concept-pct">' + c.pct + '%</span>'
           +   '<span class="concept-count">' + c.correct + ' / ' + c.total + '</span></div>'
           + '</li>';
    }).join('');
    el.innerHTML = '<ul class="concept-list">' + rows + '</ul>';
  }

  window.recordConceptResults = recordConceptResults;
  window.renderConceptPanel = renderConceptPanel;

  /* ═══════════════════════════════════════════════════════════════════
     #6 — Pacing indicator (timed exam mode only)
     ═══════════════════════════════════════════════════════════════════ */
  function updatePacing() {
    const pill = document.getElementById('pacing-pill');
    if (!pill || !window.state) return;
    const s = window.state;
    if (s.mode !== 'exam') { pill.style.display = 'none'; return; }
    const total = s.questions.length;
    const answered = Object.keys(s.answers).length;
    const totalTime = 7200; // matches initExamUI for exam mode
    const elapsed = totalTime - s.timerSeconds;
    if (elapsed < 30) { pill.style.display = 'none'; return; } // wait until they've started

    const expectedAnswered = (elapsed / totalTime) * total;
    const delta = answered - expectedAnswered;

    let cls, label;
    if (delta >= 1.5)      { cls = 'pacing-ahead';   label = 'Ahead of pace'; }
    else if (delta >= -1)  { cls = 'pacing-onpace';  label = 'On pace'; }
    else if (delta >= -3)  { cls = 'pacing-slow';    label = 'Slightly slow'; }
    else                   { cls = 'pacing-behind';  label = 'Falling behind'; }

    pill.className = 'pacing-pill ' + cls;
    pill.style.display = 'inline-flex';
    pill.innerHTML = icon('target', { size: 12 }) + ' ' + label;
    pill.title = 'You\'ve answered ' + answered + ' of ' + total + ' (expected ~' + Math.round(expectedAnswered) + ')';
  }
  window.updatePacing = updatePacing;

  /* ═══════════════════════════════════════════════════════════════════
     #9 — Onboarding (first-run flow)
     ═══════════════════════════════════════════════════════════════════ */
  async function maybeShowOnboarding() {
    const onboarded = await dbGet('pca:onboarded');
    const stats     = (await dbGet('pca:stats')) || { sessions: 0 };
    const card = document.getElementById('onboarding-card');
    if (!card) return;
    if (onboarded || stats.sessions > 0) {
      card.style.display = 'none';
      return;
    }
    card.style.display = 'block';
  }

  async function dismissOnboarding() {
    await dbSet('pca:onboarded', true);
    const card = document.getElementById('onboarding-card');
    if (card) card.style.display = 'none';
  }

  async function startDiagnostic() {
    // 10 random questions from the seed pool — no AI call needed for first session.
    const seed = (await dbGet('pca:seed-questions')) || [];
    if (seed.length === 0) {
      if (window.showToast) window.showToast('No seed questions available — please reload');
      return;
    }
    const shuffled = [].concat(seed).sort(() => Math.random() - 0.5).slice(0, Math.min(10, seed.length));
    if (window.state) {
      window.state.mode = 'practice';   // formative, with feedback
      window.state.questions = shuffled;
    }
    await dbSet('pca:onboarded', true);
    const card = document.getElementById('onboarding-card');
    if (card) card.style.display = 'none';
    if (typeof window.initExamUI === 'function') window.initExamUI();
  }

  window.maybeShowOnboarding = maybeShowOnboarding;
  window.dismissOnboarding = dismissOnboarding;
  window.startDiagnostic = startDiagnostic;

  /* ═══════════════════════════════════════════════════════════════════
     #10 — History pruning (keeps pca:history bounded)
     ═══════════════════════════════════════════════════════════════════ */
  const HISTORY_LIMIT = 50;
  async function pruneHistory() {
    const hist = (await dbGet('pca:history')) || [];
    if (hist.length <= HISTORY_LIMIT) return;
    const archived = (await dbGet('pca:history-archive')) || [];
    const toArchive = hist.slice(HISTORY_LIMIT);
    await dbSet('pca:history-archive', archived.concat(toArchive));
    await dbSet('pca:history', hist.slice(0, HISTORY_LIMIT));
  }
  window.pruneHistory = pruneHistory;

  /* ═══════════════════════════════════════════════════════════════════
     Collapsible expansion panels (Domain Mastery + Top Missed Concepts)
     – default closed; click the trigger to expand/collapse smoothly.
     – uses [aria-expanded] + .is-open for state.
     ═══════════════════════════════════════════════════════════════════ */
  function setCollapsibleOpen(panel, open) {
    const trigger = panel.querySelector('.collapsible-trigger');
    panel.classList.toggle('is-open', open);
    if (trigger) trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  function initCollapsibles() {
    document.querySelectorAll('[data-collapsible]').forEach((panel) => {
      if (panel.dataset.collapsibleBound === '1') return;
      panel.dataset.collapsibleBound = '1';
      const trigger = panel.querySelector('.collapsible-trigger');
      if (!trigger) return;
      trigger.addEventListener('click', () => {
        setCollapsibleOpen(panel, !panel.classList.contains('is-open'));
      });
      // Default state: closed
      setCollapsibleOpen(panel, false);
    });
  }

  /* Update the meta line under each collapsible title with live counts. */
  async function refreshCollapsibleMeta() {
    // Heatmap meta — count domains with ≥1 attempt
    const hm = document.getElementById('heatmap-meta');
    if (hm) {
      const stats = (await dbGet('pca:domain-mastery')) || {};
      const tracked = Object.values(stats).filter(d => d && d.total > 0).length;
      hm.textContent = tracked === 0
        ? 'No data yet — finish a session to populate'
        : tracked + (tracked === 1 ? ' domain tracked · click to view' : ' domains tracked · click to view');
    }
    // Concept meta — count concepts with ≥2 attempts
    const cm = document.getElementById('concept-meta');
    if (cm) {
      const m = (await dbGet('pca:concept-mastery')) || {};
      const tracked = Object.values(m).filter(d => d && d.total >= 2).length;
      cm.textContent = tracked === 0
        ? 'Concept mastery appears after 2+ attempts per concept'
        : tracked + (tracked === 1 ? ' concept tracked · click to view' : ' concepts tracked · click to view');
    }
  }

  // Bind on DOM-ready (script is `defer`, but be safe)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCollapsibles);
  } else {
    initCollapsibles();
  }

  window.initCollapsibles = initCollapsibles;
  window.refreshCollapsibleMeta = refreshCollapsibleMeta;
})();
