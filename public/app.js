let state = {
  mode: 'exam',
  questions: [],
  answers: {},
  confidence: {}, // Tracks 'sure' or 'guess'
  current: 0,
  timerSeconds: 7200,
  timerInterval: null,
  finished: false,
  globalDomainStats: {},
  spacedRepetitionDue: [],
  failedThisSession: [] // Temporarily holds targets for Remediation Brief
};
// Expose for enhancements.js (let-declared identifiers don't attach to window automatically).
window.state = state;

// Tiny local fallback if enhancements.js / DOMPurify failed to load.
function _safeHtml(el, text) {
  if (window.renderMdInto) return window.renderMdInto(el, text || '');
  el.textContent = text == null ? '' : String(text);
}

// ── DB Helpers ──
async function dbGet(key) {
  try { const r = await fetch(`/api/db/${key}`); if(!r.ok) return null; return (await r.json()).value; } catch { return null; }
}
async function dbSet(key, val) {
  try { await fetch(`/api/db/${key}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: val }) }); } catch {}
}

// ── Dashboard Init ──
window.addEventListener('load', async () => {
  if (window.loadFlags) await window.loadFlags();
  await renderDashboard();
  if (window.maybeShowOnboarding) await window.maybeShowOnboarding();
});

async function renderDashboard() {
  const stats = await dbGet('pca:stats') || { sessions: 0, bestScore: null };
  document.getElementById('home-sessions').textContent = stats.sessions;
  document.getElementById('home-bestscore').textContent = stats.bestScore !== null ? stats.bestScore + '%' : '—';
  
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  document.getElementById('home-total').textContent = seed.length + extra.length;

  // Render Heatmap — progress-ring cards, tone-aware (M3 surface containers)
  state.globalDomainStats = await dbGet('pca:domain-mastery') || {};
  const grid = document.getElementById('heatmap-grid');
  const entries = Object.entries(state.globalDomainStats).filter(([, d]) => d && d.total > 0);

  if (entries.length === 0) {
    grid.innerHTML =
      `<div class="heat-empty">
         <div class="heat-empty-ico" data-icon="chart"></div>
         <div>
           <strong>Your mastery heatmap is empty.</strong>
           <p>Finish your first session and we'll start tracking each domain here.</p>
         </div>
       </div>`;
  } else {
    // Sort weakest-first (only among confident-enough samples), and tail with low-data domains
    entries.sort((a, b) => {
      const [, A] = a, [, B] = b;
      const aPct = A.correct / A.total, bPct = B.correct / B.total;
      const aLow = A.total < 5, bLow = B.total < 5;
      if (aLow !== bLow) return aLow ? 1 : -1;          // confident samples first
      return aPct - bPct;                                // weakest first
    });

    grid.innerHTML = entries.map(([domain, data]) => {
      const pct      = Math.round((data.correct / data.total) * 100);
      const total    = data.total;
      // Confidence tier — colors only "earned" once we have ≥5 attempts.
      const lowData  = total < 5;
      let tier;
      if (lowData)         tier = 'learning';
      else if (pct < 60)   tier = 'red';
      else if (pct < 80)   tier = 'yellow';
      else                 tier = 'green';
      const safeDomain = escapeText(domain.replace('Case Study: ', 'CS: '));

      // SVG progress ring (radius 22, circumference ≈ 138.23)
      const C = 2 * Math.PI * 22;
      const offset = C * (1 - Math.min(pct, 100) / 100);

      const subLabel = lowData
        ? `${data.correct}/${total} so far · keep going`
        : `${data.correct} correct of ${total}`;

      return `<div class="heat-box tier-${tier}" role="group" aria-label="${safeDomain} — ${pct}% mastery (${data.correct} of ${total})">
        <div class="heat-ring" aria-hidden="true">
          <svg viewBox="0 0 56 56" width="56" height="56">
            <circle class="heat-ring-track" cx="28" cy="28" r="22"></circle>
            <circle class="heat-ring-fill"  cx="28" cy="28" r="22"
                    stroke-dasharray="${C.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}"></circle>
          </svg>
          <span class="heat-ring-pct">${pct}<span class="heat-ring-pct-sym">%</span></span>
        </div>
        <div class="heat-body">
          <div class="heat-title">${safeDomain}</div>
          <div class="heat-sub">${subLabel}</div>
        </div>
      </div>`;
    }).join('');
  }

  // Check Spaced Repetition (Daily Review)
  const srDB = await dbGet('pca:spaced-repetition') || [];
  const now = Date.now();
  state.spacedRepetitionDue = srDB.filter(item => item.nextReview <= now);

  const srBanner = document.getElementById('daily-review-banner');
  if (state.spacedRepetitionDue.length > 0) {
    srBanner.style.display = 'block';
    document.getElementById('due-count').textContent = state.spacedRepetitionDue.length;
  } else {
    srBanner.style.display = 'none';
  }

  // Concept-level mastery panel (#3)
  if (window.renderConceptPanel) await window.renderConceptPanel('concept-panel');

  // Flagged-questions count on the mode card (#4)
  const flaggedCountEl = document.getElementById('flagged-count');
  if (flaggedCountEl) {
    const flags = (await dbGet('pca:flags')) || [];
    flaggedCountEl.textContent = flags.length === 0
      ? "Practice questions you've starred"
      : flags.length + ' flagged · ready to practice';
  }

  // Refresh collapsible meta lines (heatmap + concept counts)
  if (window.refreshCollapsibleMeta) await window.refreshCollapsibleMeta();
}

// ── Flow Controllers ──
function selectMode(m) {
  state.mode = m;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
  // Try the full id first (mode-flagged, mode-adaptive), then fall back to first segment.
  const full = document.getElementById('mode-' + m);
  const short = document.getElementById('mode-' + m.split('-')[0]);
  (full || short)?.classList.add('selected');
}

async function startSession() {
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  const pool = [...seed, ...extra];

  if (state.mode === 'adaptive') {
    return startAdaptiveSprint(); // AI generation route
  } else {
    // Standard Exam/Practice: 50 random questions (case-study questions still appear here via their `caseContext`)
    state.questions = shuffle(pool).slice(0, Math.min(50, pool.length));
  }
  
  initExamUI();
}

async function startAdaptiveSprint() {
  state.mode = 'adaptive';
  showToast("🧠 AI analyzing weak spots. Generating a targeted 10-question sprint...");
  
  // Find top weak concepts
  const srDB = await dbGet('pca:spaced-repetition') || [];
  let targets = srDB.slice(0, 3).map(i => ({ domain: i.domain, text: i.text }));
  if (targets.length === 0) targets = [{ domain: "Networking", text: "Hybrid connectivity routing" }]; // Fallback

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'adaptive', targets })
    });
    const parsed = parseAIResponse((await res.json()).text);
    if (parsed.length > 0) {
      const existing = await dbGet('pca:ai-questions') || [];
      await dbSet('pca:ai-questions', [...existing, ...parsed]);
      state.questions = parsed;
      initExamUI();
    }
  } catch (err) { showToast("⚠️ Adaptive generation failed. Try practice mode."); }
}

async function startDailyReview() {
  state.mode = 'daily_review';
  showToast("⏳ Fetching your due Spaced Repetition items...");
  try {
    const targets = state.spacedRepetitionDue.map(i => ({ domain: i.domain, text: i.text }));
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'daily_review', targets })
    });
    const parsed = parseAIResponse((await res.json()).text);
    if (parsed.length > 0) {
      state.questions = parsed;
      initExamUI();
    }
  } catch (err) { showToast("⚠️ Failed to generate review."); }
}

function parseAIResponse(rawTxt) {
  try {
    let text = rawTxt.replace(/^```json\s*/im, '').replace(/\s*```\s*$/im, '').trim();
    return JSON.parse(text.slice(text.indexOf('[')));
  } catch(e) { return []; }
}

function initExamUI() {
  state.answers = {};
  state.confidence = {};
  state.current = 0;
  state.finished = false;
  state.failedThisSession = [];
  state.timerSeconds = state.mode === 'exam' ? 7200 : 1800; 
  
  showScreen('screen-exam');
  document.getElementById('exam-mode-badge').textContent = state.mode.replace('_', ' ').toUpperCase();

  // Reset timer visual state between sessions
  const tDisp = document.getElementById('timer-display');
  tDisp.classList.remove('warning', 'danger');
  tDisp.style.color = '';

  if (state.mode === 'exam') startTimer();
  else { tDisp.textContent = 'UNTIMED'; tDisp.style.color = 'var(--g-green)'; }
  
  renderQuestion();
}

function shuffle(arr) { const a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]} return a; }

// ── Render & Interaction ──
function renderQuestion() {
  const q = state.questions[state.current];
  const answered = state.answers[state.current] !== undefined;

  // Whitelist diff so it can't break out of the class attribute, and escape user-derived strings.
  const safeDiff = ['easy','medium','hard','challenging'].includes(q.diff) ? q.diff : null;
  const diffTag = safeDiff ? `<span class="tag diff-${safeDiff}">${safeDiff.toUpperCase()}</span>` : '';
  document.getElementById('q-meta').innerHTML =
    `<span class="tag domain">${escapeText(q.domain)}</span>${diffTag}` +
    `<span class="tag">Q ${state.current + 1} / ${state.questions.length}</span>`;

  // Case-study context (Markdown-aware, sanitized)
  const caseEl = document.getElementById('case-ctx');
  if (q.caseContext) {
    caseEl.style.display = 'block';
    caseEl.innerHTML = '<h4>Case Context</h4><div id="case-ctx-body"></div>';
    _safeHtml(document.getElementById('case-ctx-body'), q.caseContext);
  } else {
    caseEl.style.display = 'none';
  }

  // Display Learning Objective if AI generated it
  const loBanner = document.getElementById('learning-objective');
  if (q.learning_objective) { loBanner.style.display = 'flex'; loBanner.textContent = q.learning_objective; }
  else { loBanner.style.display = 'none'; }

  // Question body: render as sanitized Markdown + optional inline image
  const qTextEl = document.getElementById('q-text');
  const imgHtml = (window.imageBlock && q.image_url) ? window.imageBlock(q.image_url, q.image_alt) : '';
  _safeHtml(qTextEl, (imgHtml ? imgHtml + '\n\n' : '') + (q.text || ''));

  const optContainer = document.getElementById('q-options');
  const showResult = answered && (state.mode === 'practice' || state.finished);

  optContainer.innerHTML = q.opts.map((o, i) => {
    let cls = 'option', keyCls = 'opt-key';
    if (answered) {
      cls += ' disabled';
      if (showResult) {
        if (i === q.answer) { cls += ' correct'; keyCls += ' ok'; }
        else if (state.answers[state.current] === i) { cls += ' wrong'; keyCls += ' bad'; }
      } else if (state.answers[state.current] === i) { cls += ' selected'; keyCls += ' sel'; }
    }
    // q.opts comes from AI-generated content — escape before embedding.
    return `<div class="${cls}" onclick="selectOption(${i})"><span class="${keyCls}">${['A','B','C','D'][i]}</span><span class="opt-text">${escapeText(o)}</span></div>`;
  }).join('');

  // Confidence Tracker (Only in Formative Modes)
  const confTracker = document.getElementById('confidence-tracker');
  if (!answered && (state.mode === 'practice' || state.mode === 'adaptive' || state.mode === 'daily_review')) {
    confTracker.style.display = 'block';
    document.querySelectorAll('input[name="conf"]').forEach(el => el.checked = false);
    document.getElementById('btn-next').disabled = true; // Force confidence selection
  } else {
    confTracker.style.display = 'none';
    document.getElementById('btn-next').disabled = false;
  }

  const expEl = document.getElementById('q-explanation');
  if (showResult && q.explanation) {
    expEl.classList.add('visible');
    _safeHtml(document.getElementById('exp-text'), q.explanation);
  } else {
    expEl.classList.remove('visible');
  }

  document.getElementById('btn-prev').disabled = state.current === 0;
  document.getElementById('btn-next').textContent = state.current === state.questions.length - 1 ? 'Finish →' : 'Next →';
  document.getElementById('exam-qcount').textContent = `Q ${state.current+1} / ${state.questions.length}`;

  const answeredPct = (Object.keys(state.answers).length / state.questions.length) * 100;
  const progBar = document.getElementById('prog-bar');
  progBar.style.width = answeredPct + '%';
  const progPct = document.getElementById('progress-pct');
  if (progPct) progPct.textContent = Math.round(answeredPct) + '%';
  const progWrap = progBar.parentElement;
  if (progWrap) progWrap.setAttribute('aria-valuenow', String(Math.round(answeredPct)));

  // Wire the flag button (#4) — re-bound per question render so it always reflects this q.
  const flagBtn = document.getElementById('flag-btn');
  if (flagBtn && window.renderFlagControl) {
    window.renderFlagControl(q.id, flagBtn);
    flagBtn.onclick = async () => {
      await window.toggleFlag(q.id);
      // Refresh Review Later pill so it reflects the new state immediately.
      if (window.refreshReviewLaterPill) window.refreshReviewLaterPill();
    };
  }

  // Refresh the "Review Later" pill count + re-render panel if it's open.
  if (window.refreshReviewLaterPill) window.refreshReviewLaterPill();

  // Pacing tick on render (#6)
  if (window.updatePacing) window.updatePacing();
}

// ════════════════════════════════════════════════════════════════
//  Save for Later & Review panel — exam/timed mode helper
// ════════════════════════════════════════════════════════════════
function _flaggedIndicesInSession() {
  const flags = (window.getFlagsCache && window.getFlagsCache()) || [];
  const set = new Set(flags);
  const out = [];
  if (!state.questions) return out;
  for (let i = 0; i < state.questions.length; i++) {
    if (set.has(state.questions[i].id)) out.push(i);
  }
  return out;
}

function refreshReviewLaterPill() {
  const pill = document.getElementById('review-later-pill');
  const badge = document.getElementById('review-count-badge');
  if (!pill || !badge) return;
  const idxs = _flaggedIndicesInSession();
  badge.textContent = String(idxs.length);
  pill.classList.toggle('has-items', idxs.length > 0);
  pill.setAttribute('aria-label', idxs.length === 0
    ? 'No questions saved for later'
    : idxs.length + ' question' + (idxs.length === 1 ? '' : 's') + ' saved for later');
  // If the panel is open, re-render its body so the list stays current.
  const panel = document.getElementById('review-later-panel');
  if (panel && panel.classList.contains('is-open')) _renderReviewLaterList();
}

function _renderReviewLaterList() {
  const listEl = document.getElementById('review-later-list');
  const subEl  = document.getElementById('review-later-sub');
  if (!listEl) return;
  const idxs = _flaggedIndicesInSession();
  if (subEl) {
    subEl.textContent = idxs.length === 0
      ? 'Tap the Flag icon on any question to add it here'
      : idxs.length + ' flagged in this session · ' + Object.keys(state.answers || {}).length + ' answered overall';
  }
  if (idxs.length === 0) {
    listEl.innerHTML = '<div class="review-later-empty">' +
      '<svg viewBox="0 0 24 24" width="40" height="40" fill="currentColor" aria-hidden="true">' +
        '<path d="M12.36 6 12.76 8H18v6h-3.36l-.4-2H7V6h5.36zM14 4H5v17h2v-7h5.6l.4 2h7V6h-5.6L14 4z"/>' +
      '</svg>' +
      '<p>Nothing saved for later yet</p>' +
      '<p style="font-size:12px; opacity:0.75; margin-top:4px;">Tap the <strong>Flag</strong> button on any question to bookmark it for review.</p>' +
      '</div>';
    return;
  }
  const cur = state.current;
  const html = idxs.map((idx) => {
    const q = state.questions[idx];
    const isCurrent  = idx === cur;
    const answered   = state.answers && state.answers[idx] !== undefined && state.answers[idx] !== null;
    const skipped    = state.answers && state.answers[idx] === null;
    const statusCls  = answered ? 'answered' : (skipped ? 'unanswered' : 'unanswered');
    const statusText = answered ? 'Answered' : (skipped ? 'Skipped' : 'Not yet');
    const text = (q.text || '').replace(/<[^>]+>/g, '');
    return '<button class="review-later-item' + (isCurrent ? ' is-current' : '') +
      '" type="button" role="listitem" data-idx="' + idx + '" onclick="jumpToReviewQuestion(' + idx + ')">' +
      '<div class="review-later-item-top">' +
        '<span class="review-later-item-num">Q ' + (idx + 1) + '</span>' +
        '<span class="review-later-domain">' + escapeText(q.domain || '') + '</span>' +
        '<span class="review-later-status ' + statusCls + '">' + statusText + '</span>' +
      '</div>' +
      '<div class="review-later-item-text">' + escapeText(text.slice(0, 140)) + (text.length > 140 ? '…' : '') + '</div>' +
    '</button>';
  }).join('');
  listEl.innerHTML = html;
}

function openReviewLater() {
  const panel   = document.getElementById('review-later-panel');
  const overlay = document.getElementById('review-later-overlay');
  if (!panel) return;
  _renderReviewLaterList();
  panel.classList.add('is-open');
  panel.setAttribute('aria-hidden', 'false');
  if (overlay) {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
  }
  // Esc to close
  document.addEventListener('keydown', _reviewLaterEscHandler);
}

function closeReviewLater() {
  const panel   = document.getElementById('review-later-panel');
  const overlay = document.getElementById('review-later-overlay');
  if (panel) {
    panel.classList.remove('is-open');
    panel.setAttribute('aria-hidden', 'true');
  }
  if (overlay) {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
  }
  document.removeEventListener('keydown', _reviewLaterEscHandler);
}

function _reviewLaterEscHandler(e) {
  if (e.key === 'Escape') closeReviewLater();
}

function jumpToReviewQuestion(idx) {
  if (!state.questions || idx < 0 || idx >= state.questions.length) return;
  state.current = idx;
  renderQuestion();
  closeReviewLater();
}

// Expose globally so HTML inline handlers + features.js callers can reach them.
window.openReviewLater       = openReviewLater;
window.closeReviewLater      = closeReviewLater;
window.jumpToReviewQuestion  = jumpToReviewQuestion;
window.refreshReviewLaterPill = refreshReviewLaterPill;

function setConfidence(val) {
  state.confidence[state.current] = val;
  if(state.answers[state.current] !== undefined) {
    document.getElementById('btn-next').disabled = false;
    if (state.current < state.questions.length - 1) setTimeout(() => navQuestion(1), 600);
  }
}

function selectOption(i) {
  if (state.answers[state.current] !== undefined) return;
  state.answers[state.current] = i;
  
  const isFormative = (state.mode === 'practice' || state.mode === 'adaptive' || state.mode === 'daily_review');
  if (isFormative && !state.confidence[state.current]) {
    showToast("Please select your confidence level below to proceed.");
    renderQuestion(); // Re-render to show selected option visually, but wait for confidence
    return;
  }
  
  renderQuestion();
  document.getElementById('btn-next').disabled = false;
  if (state.mode === 'exam' && state.current < state.questions.length - 1) setTimeout(() => navQuestion(1), 1000);
  else if (isFormative && state.current < state.questions.length - 1) setTimeout(() => navQuestion(1), 2000); // Give time to read explanation
}

function skipQuestion() { 
  if (state.answers[state.current] === undefined) { 
    state.answers[state.current] = null; 
    state.confidence[state.current] = 'guess'; // Skip = Guess
    if(state.current < state.questions.length-1) navQuestion(1); 
  } 
}

function navQuestion(dir) { 
  const next = state.current + dir; 
  if (next < 0 || next >= state.questions.length) { 
    if(next>=state.questions.length) confirmFinish(); 
    return; 
  } 
  state.current = next; 
  renderQuestion(); 
}

// ── Test-Teach-Retest & Finish Logic ──
function startTimer() {
  clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    state.timerSeconds--;
    const el = document.getElementById('timer-display');
    el.textContent = `${Math.floor(state.timerSeconds/3600)}:${String(Math.floor((state.timerSeconds%3600)/60)).padStart(2,'0')}:${String(state.timerSeconds%60).padStart(2,'0')}`;
    // Color cue
    if (state.timerSeconds <= 600) el.classList.add('danger');
    else if (state.timerSeconds <= 1800) { el.classList.remove('danger'); el.classList.add('warning'); }
    // Pacing every 5s to keep the indicator current (#6)
    if (state.timerSeconds % 5 === 0 && window.updatePacing) window.updatePacing();
    if (state.timerSeconds <= 0) { clearInterval(state.timerInterval); confirmFinish(true); }
  }, 1000);
}

function confirmFinish(force = false) {
  const unans = state.questions.length - Object.keys(state.answers).filter(k => state.answers[k] !== null).length;
  if (unans > 0 && !force && !confirm(`Finish with ${unans} unanswered questions?`)) return;
  processSessionEnd();
}

async function processSessionEnd() {
  clearInterval(state.timerInterval);
  state.finished = true;

  let correct = 0;
  let srDB = await dbGet('pca:spaced-repetition') || [];
  state.failedThisSession = [];

  state.questions.forEach((q, i) => {
    const ans = state.answers[i];
    const conf = state.confidence[i];
    const isCorrect = (ans === q.answer);
    
    // Confidence-based assessment: A correct guess is treated as a weakness.
    if (isCorrect) correct++;
    
    if (!isCorrect || conf === 'guess') {
      state.failedThisSession.push(q);
      
      // Update Spaced Repetition (Daily Review) DB
      const existingIdx = srDB.findIndex(x => x.id === q.id);
      if (existingIdx > -1) {
        srDB[existingIdx].nextReview = Date.now() + 86400000; // Reset to 1 day
      } else {
        srDB.push({ id: q.id, domain: q.domain, text: q.text, nextReview: Date.now() + 86400000 });
      }
    } else {
      // They knew it and got it right. If it was in SR, increase interval (or remove).
      const existingIdx = srDB.findIndex(x => x.id === q.id);
      if (existingIdx > -1) srDB.splice(existingIdx, 1); // For simplicity, removing from SR queue if mastered.
    }
  });

  await dbSet('pca:spaced-repetition', srDB);

  // Teach Phase: Trigger Remediation Brief if they failed concepts
  if (state.failedThisSession.length > 0 && (state.mode === 'adaptive' || state.mode === 'daily_review')) {
    showRemediationModal();
  } else {
    showResultsScreen(correct);
  }
}

async function showRemediationModal() {
  document.getElementById('remediation-modal').classList.add('active');
  const briefText = document.getElementById('remediation-text');
  briefText.innerHTML = '<div class="spinner"></div> Analyzing your weak spots...';
  
  try {
    const topics = state.failedThisSession.slice(0, 3).map(q => q.domain + ": " + q.text.substring(0,50));
    const res = await fetch('/api/brief', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topics })
    });
    const html = (await res.json()).html || '';
    // The brief may be HTML or Markdown — pipe through the safe renderer either way.
    _safeHtml(briefText, html);
  } catch (e) {
    briefText.innerHTML = "<p>Connection error. Proceed to standard review.</p>";
  }
}

function proceedToResultsOrRetest() {
  document.getElementById('remediation-modal').classList.remove('active');
  const correct = Object.keys(state.answers).filter(i => state.answers[i] === state.questions[i].answer).length;
  showResultsScreen(correct);
}

async function showResultsScreen(correct) {
  const scorePct = state.questions.length > 0 ? Math.round((correct / state.questions.length) * 100) : 0;
  document.getElementById('score-circle').className = 'score-circle' + (scorePct >= 72 ? ' pass' : '');
  document.getElementById('score-pct').textContent = scorePct + '%';
  document.getElementById('result-title').textContent = scorePct >= 72 ? '🎉 Target Hit!' : '📚 Remediation Needed';

  // Save the session data before showing the screen
  await saveSession(scorePct, state.questions.length, state.answers, state.questions);

  showScreen('screen-results');
}

// ── Session Saving & History (Admin Logs) ──
async function saveSession(score, total, answers, questions) {
  try {
    const stats = await dbGet('pca:stats') || { sessions: 0, bestScore: null };
    stats.sessions++;
    if (stats.bestScore === null || score > stats.bestScore) stats.bestScore = score;
    await dbSet('pca:stats', stats);

    // Calculate weakest domain for this specific session
    const domMap = {};
    questions.forEach((q, i) => {
      const isCorrect = answers[i] === q.answer;
      if (!domMap[q.domain]) domMap[q.domain] = { total: 0, correct: 0 };
      domMap[q.domain].total++;
      if (isCorrect) domMap[q.domain].correct++;
    });

    let weakestDomain = "None";
    let lowestPct = 100;
    for (let [d, data] of Object.entries(domMap)) {
      if (data.total > 0) {
        let pct = (data.correct / data.total) * 100;
        if (pct < lowestPct) { lowestPct = pct; weakestDomain = d; }
      }
    }

    const session = {
      date: new Date().toISOString(),
      score,
      total,
      weakestDomain: `${weakestDomain} (${Math.round(lowestPct)}%)`
    };

    await dbSet('pca:last-session', session);

    // Save to historical log for the Admin screen
    const history = await dbGet('pca:history') || [];
    history.unshift(session); // Add newest to the top
    await dbSet('pca:history', history);

    // #3 — Roll up concept mastery from this session
    if (window.recordConceptResults) {
      try { await window.recordConceptResults(questions, answers); } catch(e) {}
    }

    // #10 — Keep history table bounded
    if (window.pruneHistory) {
      try { await window.pruneHistory(); } catch(e) {}
    }

    // Mark first-run onboarding satisfied once a session has been saved
    await dbSet('pca:onboarded', true);

    const reviewBtn = document.getElementById('review-btn-home');
    if(reviewBtn) reviewBtn.style.display = 'inline';
  } catch(e) {
    console.error("Failed to save session", e);
  }
}

// ── Review & Navigation ──
async function goReview() {
  const list = document.getElementById('review-list');
  list.innerHTML = ''; // clear; we append nodes to keep Markdown rendering sandboxed

  state.questions.forEach((q, i) => {
    const userAns = state.answers[i];
    const ok = userAns === q.answer;
    const stat = userAns == null ? 'SKIPPED' : ok ? 'CORRECT' : 'WRONG';
    const pillCls = ok ? 'ok' : userAns == null ? 'skip' : 'bad';

    const wrap = document.createElement('div');
    wrap.className = 'review-q';
    wrap.innerHTML = `
      <div class="q-num"><span>Q${i+1} · ${escapeText(q.domain)}</span><span class="pill ${pillCls}">${stat}</span></div>
      <div class="q-txt" data-slot="text"></div>
      <div class="review-answer-block">
        <div class="review-line"><span class="review-label">Your answer:</span>
          <span class="${ok ? 'review-ok' : 'review-bad'}">${userAns != null ? escapeText(q.opts[userAns]) : 'None'}</span>
        </div>
        ${!ok ? `<div class="review-line"><span class="review-label">Correct:</span>
          <span class="review-ok">${escapeText(q.opts[q.answer])}</span></div>` : ''}
        ${q.explanation ? `<div class="review-expl" data-slot="expl"></div>` : ''}
        ${(!ok && userAns != null)
          ? `<button class="btn-tutor" data-q-idx="${i}" data-wrong-idx="${userAns}">Ask AI Tutor</button>
             <div id="tutor-box-${i}" class="ai-tutor-box"></div>` : ''}
      </div>`;
    // Fill Markdown-rendered slots safely
    const txtSlot = wrap.querySelector('[data-slot="text"]');
    if (txtSlot) {
      const img = (window.imageBlock && q.image_url) ? window.imageBlock(q.image_url, q.image_alt) : '';
      _safeHtml(txtSlot, (img ? img + '\n\n' : '') + (q.text || ''));
    }
    const explSlot = wrap.querySelector('[data-slot="expl"]');
    if (explSlot && q.explanation) _safeHtml(explSlot, q.explanation);

    // Wire tutor button without embedding user-controlled strings in HTML
    const tutorBtn = wrap.querySelector('button.btn-tutor');
    if (tutorBtn) {
      tutorBtn.addEventListener('click', () => {
        const wrongIdx = parseInt(tutorBtn.getAttribute('data-wrong-idx'), 10);
        askTutor(i, q.opts[wrongIdx], q.opts[q.answer]);
      });
    }
    list.appendChild(wrap);
  });
  showScreen('screen-review');
}

function escapeText(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}

// ═══════════════════════════════════════════════
//  ADMIN & ANALYTICS DASHBOARD
// ═══════════════════════════════════════════════
async function showAdmin() {
  showScreen('screen-admin');

  const history = await dbGet('pca:history') || [];

  let passes = 0;
  let failures = 0;

  const listHtml = history.map(h => {
    const isPass = h.score >= 72;
    if (isPass) passes++; else failures++;

    const date = new Date(h.date).toLocaleDateString() + ' ' + new Date(h.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    return `<tr>
      <td>${date}</td>
      <td style="font-family:var(--font);">${h.score}%</td>
      <td><span class="status-badge ${isPass ? 'pass' : 'fail'}">${isPass ? 'PASS' : 'FAIL'}</span></td>
      <td class="weak-domain-text">${h.weakestDomain}</td>
    </tr>`;
  }).join('');

  document.getElementById('admin-total-sessions').textContent = history.length;
  document.getElementById('admin-failures').textContent = failures;
  document.getElementById('admin-passes').textContent = passes;

  const listEl = document.getElementById('admin-history-list');
  if (history.length === 0) {
    listEl.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--muted);">No session history available yet.</td></tr>`;
  } else {
    listEl.innerHTML = listHtml;
  }
}

async function forceAIFetch() {
  const btn = document.getElementById('admin-fetch-btn');
  const statusEl = document.getElementById('admin-ai-status');
  const includeDetailedTutor = document.getElementById('admin-ai-force-cb').checked;

  btn.disabled = true;
  btn.textContent = "Generating...";
  statusEl.style.display = "block";
  statusEl.style.color = "var(--yellow)";
  statusEl.textContent = "Analyzing history and generating new questions...";

  // Get weak domains from global stats
  const domStats = state.globalDomainStats || await dbGet('pca:domain-mastery') || {};
  let weak = [];
  for (let [d, data] of Object.entries(domStats)) {
    if (data.total >= 3 && (data.correct / data.total) < 0.65) weak.push(d);
  }
  if (weak.length === 0) weak = ['Networking', 'Security & Compliance'];

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // Pass the tutor flag to backend if you want to alter the prompt
      body: JSON.stringify({ type: 'adaptive', targets: weak.map(w => ({domain: w, text: "Admin forced generation"})) })
    });

    const rawTxt = (await res.json()).text;
    let text = rawTxt.replace(/^```json\s*/im, '').replace(/\s*```\s*$/im, '').trim();
    const parsed = JSON.parse(text.slice(text.indexOf('[')));

    if (parsed.length > 0) {
      const existing = await dbGet('pca:ai-questions') || [];
      await dbSet('pca:ai-questions', [...existing, ...parsed]);

      statusEl.style.color = "var(--green)";
      statusEl.textContent = `✅ Successfully fetched ${parsed.length} new questions targeting ${weak.join(', ')}!`;
    } else {
      throw new Error("No questions parsed");
    }
  } catch (err) {
    statusEl.style.color = "var(--red)";
    if (err.message.includes("429") || err.status === 429) {
       statusEl.textContent = "⏳ Rate limit reached. Please wait 60 seconds and try again.";
    } else {
       statusEl.textContent = "⚠️ Failed to fetch questions. Check server logs.";
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "Fetch New Questions Now";
  }
}


async function askTutor(qIndex, wrongText, correctText) {
  const box = document.getElementById(`tutor-box-${qIndex}`);
  box.classList.add('visible');
  box.innerHTML = `<em>AI Tutor is analyzing your answer…</em>`;
  try {
    const res = await fetch('/api/tutor', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ question: state.questions[qIndex].text, correct: correctText, wrong: wrongText })
    });
    const txt = (await res.json()).text || '';
    // Preserve the "AI Tutor Analysis" heading, then render the response as sanitized Markdown.
    box.innerHTML = '<strong>AI Tutor Analysis</strong><div data-slot="body"></div>';
    _safeHtml(box.querySelector('[data-slot="body"]'), txt);
  } catch (e) {
    box.innerHTML = `<strong>AI Tutor Analysis</strong>Tutor offline. Please retry shortly.`;
  }
}

function showScreen(id) { document.querySelectorAll('.screen').forEach(s => s.classList.remove('active')); document.getElementById(id).classList.add('active'); }
async function goHome() { clearInterval(state.timerInterval); await renderDashboard(); showScreen('screen-home'); }
function showToast(msg) { const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 3000); }
async function confirmGoHome() { if(Object.keys(state.answers).length > 0 && !state.finished && !confirm('Quit? Progress lost.')) return; await goHome(); }