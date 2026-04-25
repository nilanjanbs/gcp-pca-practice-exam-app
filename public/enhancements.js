/* ═══════════════════════════════════════════════════════════════════
   enhancements.js — two feature bundles layered on top of app.js:

   (A) Safe Markdown/Mermaid/image renderer
       → window.md(text)           → sanitized HTML string
       → window.renderMdInto(el,t) → sets element.innerHTML + runs mermaid

   (B) Adaptive-Sprint transparency
       → window.openAdaptivePreview()   — called from the home-screen card
       → window.confirmAdaptiveSprint() — fires the real /api/generate

   Loaded BEFORE app.js so app.js can call window.md / window.renderMdInto.
   ═══════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─────────────────── (A) Markdown renderer ─────────────────── */

  // Configure marked: treat ```mermaid blocks specially so we can render diagrams.
  if (window.marked) {
    const renderer = new marked.Renderer();
    const origCode = renderer.code.bind(renderer);
    renderer.code = function (code, infostring) {
      const lang = ((infostring || '') + '').trim().split(/\s+/)[0];
      if (lang === 'mermaid') {
        // Encode so DOMPurify keeps the content verbatim inside the div.
        return '<div class="mermaid">' + escapeHtml(code) + '</div>';
      }
      return origCode(code, infostring);
    };
    marked.setOptions({ breaks: true, gfm: true });
    marked.use({ renderer });
  }

  // Init Mermaid once, honoring the current theme.
  if (window.mermaid) {
    const theme = document.documentElement.getAttribute('data-theme')
                  || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default');
    mermaid.initialize({
      startOnLoad: false,
      theme: theme === 'dark' ? 'dark' : 'default',
      securityLevel: 'strict',
      fontFamily: "'Roboto', 'Google Sans', system-ui, sans-serif"
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
    });
  }

  // Render markdown → sanitized HTML. Safe for untrusted content.
  function md(text) {
    if (text == null) return '';
    const raw = typeof text === 'string' ? text : String(text);
    let html;
    try {
      html = window.marked ? marked.parse(raw) : escapeHtml(raw).replace(/\n/g, '<br>');
    } catch (e) {
      html = escapeHtml(raw);
    }
    if (!window.DOMPurify) return html;
    // Allow class on divs (needed for .mermaid) and common inline tags/code/tables.
    return DOMPurify.sanitize(html, {
      ADD_ATTR: ['target', 'rel', 'class'],
      FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input'],
      FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus']
    });
  }

  // Render markdown into an element and run Mermaid on any diagram blocks.
  async function renderMdInto(el, text) {
    if (!el) return;
    el.innerHTML = md(text);
    if (window.mermaid) {
      const diagrams = el.querySelectorAll('.mermaid');
      if (diagrams.length) {
        try {
          await mermaid.run({ nodes: diagrams });
        } catch (e) { /* bad diagram syntax — leave as code */ }
      }
    }
  }

  // Build the optional inline <figure> for q.image_url.
  function imageBlock(url, alt) {
    if (!url || typeof url !== 'string') return '';
    // Only allow http(s) or data: urls to avoid javascript: injections.
    if (!/^(https?:|data:image\/)/i.test(url)) return '';
    const safeAlt = escapeHtml(alt || 'Question diagram');
    const safeUrl = escapeHtml(url);
    return '<figure class="q-image"><img src="' + safeUrl + '" alt="' + safeAlt + '" loading="lazy"></figure>';
  }

  window.md = md;
  window.renderMdInto = renderMdInto;
  window.imageBlock = imageBlock;

  /* ─────────────── (B) Adaptive-Sprint transparency ─────────────── */

  // Compute which domains to target, with WHY metadata for the UI.
  // Priority: spaced-repetition (explicit failures) → domain mastery (cold data) → fallback.
  async function computeAdaptiveTargets() {
    const domainStats = (window.state && window.state.globalDomainStats) || {};
    let weakDomains = [];

    // Rank domains by lowest correctness, minimum 2 attempts.
    const ranked = Object.entries(domainStats)
      .filter(([_, d]) => d && d.total >= 2)
      .map(([name, d]) => ({
        name: name,
        attempts: d.total,
        correct: d.correct,
        pct: Math.round((d.correct / d.total) * 100)
      }))
      .sort((a, b) => a.pct - b.pct);

    // Take up to 3 domains with < 80% mastery.
    weakDomains = ranked.filter(d => d.pct < 80).slice(0, 3);

    // Pull spaced-repetition concepts to enrich targets with a sample missed-concept.
    const srDB = await dbGetSafe('pca:spaced-repetition') || [];
    const byDomain = {};
    srDB.forEach(item => {
      if (!byDomain[item.domain]) byDomain[item.domain] = [];
      byDomain[item.domain].push(item.text);
    });

    let targets;
    if (weakDomains.length > 0) {
      targets = weakDomains.map(d => ({
        domain: d.name,
        pct: d.pct,
        attempts: d.attempts,
        sample: (byDomain[d.name] && byDomain[d.name][0])
                || '(general concepts in this domain)',
        reason: d.pct < 50 ? 'Critical weak area'
              : d.pct < 65 ? 'Below passing threshold'
              : 'Room to improve'
      }));
    } else if (srDB.length > 0) {
      // No stats yet but have SR items.
      targets = srDB.slice(0, 3).map(i => ({
        domain: i.domain,
        pct: null,
        attempts: null,
        sample: i.text,
        reason: 'Recently missed'
      }));
    } else {
      // Cold-start fallback.
      targets = [{
        domain: 'Networking',
        pct: null,
        attempts: null,
        sample: 'Hybrid connectivity routing',
        reason: 'Cold-start — no session history yet'
      }];
    }
    return targets;
  }

  async function dbGetSafe(key) {
    try {
      const r = await fetch('/api/db/' + key);
      if (!r.ok) return null;
      return (await r.json()).value;
    } catch (e) { return null; }
  }

  // ── Modal state machine ──
  let cachedTargets = [];

  async function openAdaptivePreview() {
    const modal = document.getElementById('adaptive-preview-modal');
    if (!modal) return; // fallback: just run legacy sprint
    showAdaptiveState('analyzing');
    modal.classList.add('active');
    cachedTargets = await computeAdaptiveTargets();
    showAdaptiveState('preview', cachedTargets);
  }

  function closeAdaptivePreview() {
    const modal = document.getElementById('adaptive-preview-modal');
    if (modal) modal.classList.remove('active');
  }

  function showAdaptiveState(state, data) {
    const body = document.getElementById('adaptive-preview-body');
    const confirmBtn = document.getElementById('adaptive-confirm-btn');
    const cancelBtn = document.getElementById('adaptive-cancel-btn');
    if (!body) return;

    if (state === 'analyzing') {
      body.innerHTML = '<div class="adp-analyzing">'
        + '<div class="spinner"></div>'
        + '<p>Analyzing your performance history…</p>'
        + '</div>';
      if (confirmBtn) confirmBtn.disabled = true;
      if (cancelBtn)  cancelBtn.disabled  = false;
      return;
    }

    if (state === 'preview') {
      const targets = data || [];
      const rows = targets.map(t => {
        const pct = t.pct != null ? t.pct + '%' : '—';
        const pctCls = t.pct == null ? 'neutral'
                       : t.pct < 50 ? 'red'
                       : t.pct < 65 ? 'yellow'
                       : t.pct < 80 ? 'yellow' : 'green';
        const attempts = t.attempts != null ? (t.attempts + ' attempts') : 'New data';
        return '<div class="adp-target">'
             +   '<div class="adp-target-head">'
             +     '<span class="adp-domain">' + escapeHtml(t.domain) + '</span>'
             +     '<span class="adp-pct ' + pctCls + '">' + pct + '</span>'
             +   '</div>'
             +   '<div class="adp-target-meta">' + escapeHtml(t.reason) + ' · ' + escapeHtml(attempts) + '</div>'
             +   '<div class="adp-sample">Concept: <em>' + escapeHtml(t.sample) + '</em></div>'
             + '</div>';
      }).join('');

      const total = targets.length * 5; // backend generates 5 per target (max)
      body.innerHTML =
          '<p class="adp-intro">The AI will generate questions targeting these <strong>'
        + targets.length + '</strong> weak area' + (targets.length === 1 ? '' : 's') + ':</p>'
        + '<div class="adp-target-list">' + rows + '</div>'
        + '<p class="adp-footnote">Expected batch: up to <strong>' + total + '</strong> new questions. '
        + 'They\'ll be added to your pool and you\'ll start immediately.</p>';
      if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.textContent = 'Generate Sprint →'; }
      if (cancelBtn)  cancelBtn.disabled = false;
      return;
    }

    if (state === 'loading') {
      const step = data && data.step || 1;
      const mkStep = (n, label) => {
        const cls = n < step ? 'done' : n === step ? 'active' : 'pending';
        const icon = n < step ? '✓' : n === step ? '●' : '○';
        return '<li class="adp-step ' + cls + '"><span class="adp-step-icon">' + icon + '</span>' + label + '</li>';
      };
      body.innerHTML =
          '<div class="adp-loading">'
        +   '<ol class="adp-steps">'
        +     mkStep(1, 'Sending targets to AI provider')
        +     mkStep(2, 'Generating scenario-based questions')
        +     mkStep(3, 'Validating and parsing response')
        +     mkStep(4, 'Saving to your question pool')
        +   '</ol>'
        +   '<div class="adp-loading-foot"><div class="spinner"></div><span>' + escapeHtml(data && data.note || 'Working…') + '</span></div>'
        + '</div>';
      if (confirmBtn) { confirmBtn.disabled = true; confirmBtn.textContent = 'Working…'; }
      if (cancelBtn)  cancelBtn.disabled = true;
      return;
    }

    if (state === 'error') {
      body.innerHTML =
          '<div class="adp-error">'
        +   '<p><strong>Generation failed.</strong> ' + escapeHtml(data || 'Unknown error.') + '</p>'
        +   '<p class="adp-footnote">You can retry, or cancel and start a Practice Mode session instead.</p>'
        + '</div>';
      if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.textContent = 'Retry →'; }
      if (cancelBtn)  cancelBtn.disabled = false;
      return;
    }
  }

  // Called when the user clicks "Generate Sprint". Replaces the old startAdaptiveSprint.
  async function confirmAdaptiveSprint() {
    if (!cachedTargets || cachedTargets.length === 0) {
      cachedTargets = await computeAdaptiveTargets();
    }

    // Step 1: prep request
    showAdaptiveState('loading', { step: 1, note: 'Calling AI provider…' });

    // Map UI targets back to the backend shape.
    const targetsPayload = cachedTargets.map(t => ({ domain: t.domain, text: t.sample }));

    try {
      showAdaptiveState('loading', { step: 2, note: 'Waiting on AI response (this can take 10–20s)…' });
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'adaptive', targets: targetsPayload })
      });

      if (!res.ok) {
        const msg = res.status === 429
          ? 'Rate limit reached. Please wait ~60 seconds.'
          : 'AI provider returned ' + res.status + '. Check server logs.';
        showAdaptiveState('error', msg);
        return;
      }

      const json = await res.json();
      showAdaptiveState('loading', { step: 3, note: 'Parsing questions…' });

      const parsed = (window.parseAIResponse || fallbackParse)(json.text || '');
      if (!parsed || parsed.length === 0) {
        showAdaptiveState('error', 'AI returned no parseable questions. Try again in a moment.');
        return;
      }

      showAdaptiveState('loading', { step: 4, note: 'Saving ' + parsed.length + ' new question' + (parsed.length === 1 ? '' : 's') + '…' });
      const existing = await dbGetSafe('pca:ai-questions') || [];
      await fetch('/api/db/pca:ai-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: existing.concat(parsed) })
      });

      // Hand off to the app state & launch the exam.
      if (window.state) {
        window.state.mode = 'adaptive';
        window.state.questions = parsed;
      }
      closeAdaptivePreview();
      if (typeof window.initExamUI === 'function') {
        window.initExamUI();
      }
    } catch (err) {
      showAdaptiveState('error', (err && err.message) || 'Network error. Please retry.');
    }
  }

  function fallbackParse(raw) {
    try {
      const t = raw.replace(/^```json\s*/im, '').replace(/\s*```\s*$/im, '').trim();
      return JSON.parse(t.slice(t.indexOf('[')));
    } catch (e) { return []; }
  }

  window.openAdaptivePreview   = openAdaptivePreview;
  window.closeAdaptivePreview  = closeAdaptivePreview;
  window.confirmAdaptiveSprint = confirmAdaptiveSprint;

  /* Re-init Mermaid when the theme toggles so diagrams match. */
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn && window.mermaid) {
    themeBtn.addEventListener('click', function () {
      setTimeout(function () {
        const t = document.documentElement.getAttribute('data-theme');
        mermaid.initialize({
          startOnLoad: false,
          theme: t === 'dark' ? 'dark' : 'default',
          securityLevel: 'strict',
          fontFamily: "'Roboto', 'Google Sans', system-ui, sans-serif"
        });
        // Force re-render any existing diagrams.
        const existing = document.querySelectorAll('.mermaid[data-processed="true"]');
        existing.forEach(el => {
          el.removeAttribute('data-processed');
          el.innerHTML = el.getAttribute('data-source') || el.innerHTML;
        });
        if (existing.length) mermaid.run({ nodes: existing }).catch(()=>{});
      }, 0);
    });
  }
})();
