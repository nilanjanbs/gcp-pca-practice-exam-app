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
window.addEventListener('load', async () => { await renderDashboard(); });

async function renderDashboard() {
  const stats = await dbGet('pca:stats') || { sessions: 0, bestScore: null };
  document.getElementById('home-sessions').textContent = stats.sessions;
  document.getElementById('home-bestscore').textContent = stats.bestScore !== null ? stats.bestScore + '%' : '—';
  
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  document.getElementById('home-total').textContent = seed.length + extra.length;

  // Render Heatmap
  state.globalDomainStats = await dbGet('pca:domain-mastery') || {};
  const grid = document.getElementById('heatmap-grid');
  grid.innerHTML = Object.keys(state.globalDomainStats).length === 0 ? '<div style="font-size:13px; color:var(--muted)">Complete a session to generate heatmap.</div>' : 
    Object.entries(state.globalDomainStats).map(([domain, data]) => {
      if (data.total < 3) return ''; 
      const pct = Math.round((data.correct / data.total) * 100);
      let cls = pct < 60 ? 'red' : pct < 80 ? 'yellow' : 'green';
      return `<div class="heat-box ${cls}"><div class="heat-title">${domain.replace('Case Study: ', 'CS: ')}</div><div class="heat-pct">${pct}%</div></div>`;
    }).join('');

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
}

// ── Flow Controllers ──
function selectMode(m) {
  state.mode = m;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
  if(document.getElementById(`mode-${m.split('-')[0]}`)) document.getElementById(`mode-${m.split('-')[0]}`).classList.add('selected');
}

async function startSession() {
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  const pool = [...seed, ...extra];

  if (state.mode === 'case-study') {
    const cases = {};
    pool.filter(q => q.caseContext).forEach(q => { if (!cases[q.domain]) cases[q.domain] = []; cases[q.domain].push(q); });
    const keys = Object.keys(cases);
    if(keys.length === 0) return showToast('No case studies found.');
    state.questions = cases[keys[Math.floor(Math.random() * keys.length)]];
  } else if (state.mode === 'adaptive') {
    return startAdaptiveSprint(); // AI generation route
  } else {
    // Standard Exam/Practice: 50 random questions
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
  
  if (state.mode === 'exam') startTimer();
  else { document.getElementById('timer-display').textContent = 'UNTIMED'; document.getElementById('timer-display').style.color = 'var(--green)'; }
  
  renderQuestion();
}

function shuffle(arr) { const a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]} return a; }

// ── Render & Interaction ──
function renderQuestion() {
  const q = state.questions[state.current];
  const answered = state.answers[state.current] !== undefined;

  const diffTag = q.diff ? `<span class="tag diff-${q.diff}">${q.diff.toUpperCase()}</span>` : '';
  document.getElementById('q-meta').innerHTML = `<span class="tag domain">${q.domain}</span>${diffTag}<span class="tag">Q ${state.current + 1} / ${state.questions.length}</span>`;

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
    return `<div class="${cls}" onclick="selectOption(${i})"><span class="${keyCls}">${['A','B','C','D'][i]}</span><span class="opt-text">${o}</span></div>`;
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
  document.getElementById('prog-bar').style.width = ((Object.keys(state.answers).length / state.questions.length) * 100) + '%';
}

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