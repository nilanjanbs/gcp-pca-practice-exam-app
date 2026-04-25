let state = {
  mode: 'exam',
  questions: [],
  answers: {},
  current: 0,
  timerSeconds: 7200,
  timerInterval: null,
  finished: false,
  globalDomainStats: {} // For heatmap
};

// ── DB Helpers ──
async function dbGet(key) {
  try { const r = await fetch(`/api/db/${key}`); if(!r.ok) return null; return (await r.json()).value; } catch { return null; }
}
async function dbSet(key, val) {
  try { await fetch(`/api/db/${key}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ value: val }) }); } catch {}
}

// ── Initialization & Dashboard ──
window.addEventListener('load', async () => {
  await renderDashboard();
});

async function renderDashboard() {
  const stats = await dbGet('pca:stats') || { sessions: 0, bestScore: null };
  document.getElementById('home-sessions').textContent = stats.sessions;
  document.getElementById('home-bestscore').textContent = stats.bestScore !== null ? stats.bestScore + '%' : '—';
  
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  document.getElementById('home-total').textContent = seed.length + extra.length;

  const lastSession = await dbGet('pca:last-session');
  if (lastSession) document.getElementById('review-btn-home').style.display = 'inline';

  // Render Domain Heatmap
  state.globalDomainStats = await dbGet('pca:domain-mastery') || {};
  const grid = document.getElementById('heatmap-grid');
  
  if (Object.keys(state.globalDomainStats).length === 0) {
    grid.innerHTML = '<div style="font-size:13px; color:var(--muted)">Complete a session to generate your heatmap.</div>';
    return;
  }

  grid.innerHTML = Object.entries(state.globalDomainStats).map(([domain, data]) => {
    if (data.total < 3) return ''; // Skip if too little data
    const pct = Math.round((data.correct / data.total) * 100);
    let colorClass = pct < 60 ? 'red' : pct < 80 ? 'yellow' : 'green';
    return `<div class="heat-box ${colorClass}">
      <div class="heat-title">${domain.replace('Case Study: ', 'CS: ')}</div>
      <div class="heat-pct">${pct}%</div>
      <div class="heat-sub">${data.correct} / ${data.total} correct</div>
    </div>`;
  }).join('');
}

// ── Exam Flow ──
function selectMode(m) {
  state.mode = m;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('selected'));
  document.getElementById(`mode-${m.split('-')[0]}`).classList.add('selected');
}

async function startExam() {
  const seed = await dbGet('pca:seed-questions') || [];
  const extra = await dbGet('pca:ai-questions') || [];
  const pool = [...seed, ...extra];

  if (state.mode === 'case-study') {
    // Group case studies and pick one randomly
    const cases = {};
    pool.filter(q => q.caseContext).forEach(q => {
      if (!cases[q.domain]) cases[q.domain] = [];
      cases[q.domain].push(q);
    });
    const keys = Object.keys(cases);
    if(keys.length === 0) { showToast('No case studies found.'); return; }
    const selected = keys[Math.floor(Math.random() * keys.length)];
    state.questions = cases[selected];
  } else {
    // Standard random mix
    state.questions = shuffle(pool).slice(0, Math.min(50, pool.length));
  }

  if (state.questions.length === 0) { showToast('No questions available.'); return; }
  initExamUI();
}

function initExamUI() {
  state.answers = {};
  state.current = 0;
  state.finished = false;
  state.timerSeconds = state.mode === 'case-study' ? 1800 : 7200; // 30 mins for case study
  
  showScreen('screen-exam');
  document.getElementById('exam-mode-badge').textContent = state.mode.toUpperCase();
  renderQuestion();
  
  if (state.mode === 'exam') startTimer();
  else { document.getElementById('timer-display').textContent = 'UNTIMED'; document.getElementById('timer-display').style.color = 'var(--green)'; }
}

function shuffle(arr) { const a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]} return a; }

// ── Render & Nav (Unchanged core logic) ──
function renderQuestion() {
  const q = state.questions[state.current];
  const answered = state.answers[state.current] !== undefined;

  document.getElementById('q-meta').innerHTML = `<span class="tag domain">${q.domain}</span><span class="tag diff-${q.diff}">${q.diff.toUpperCase()}</span><span class="tag">Q ${state.current + 1} / ${state.questions.length}</span>`;
  
  const ctx = document.getElementById('case-ctx');
  if (q.caseContext) { ctx.style.display = 'block'; ctx.innerHTML = `<h4>📋 Case Study Context</h4>${q.caseContext}`; } 
  else ctx.style.display = 'none';

  document.getElementById('q-text').innerHTML = q.text;

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

  const expEl = document.getElementById('q-explanation');
  if (showResult && q.explanation) { expEl.classList.add('visible'); document.getElementById('exp-text').textContent = q.explanation; } 
  else expEl.classList.remove('visible');

  document.getElementById('btn-prev').disabled = state.current === 0;
  document.getElementById('btn-next').textContent = state.current === state.questions.length - 1 ? 'Finish →' : 'Next →';
  document.getElementById('btn-skip').style.display = answered ? 'none' : 'inline';
  document.getElementById('exam-qcount').textContent = `Q ${state.current+1} / ${state.questions.length}`;
  
  const pct = (Object.keys(state.answers).length / state.questions.length) * 100;
  document.getElementById('prog-bar').style.width = pct + '%';
  document.getElementById('prog-frac').textContent = `${Object.keys(state.answers).length} / ${state.questions.length}`;
}

function selectOption(i) {
  if (state.answers[state.current] !== undefined) return;
  state.answers[state.current] = i;
  renderQuestion();
  if (state.mode === 'exam' && state.current < state.questions.length - 1) setTimeout(() => navQuestion(1), 1200);
}
function skipQuestion() { if (state.answers[state.current] === undefined) { state.answers[state.current] = null; if(state.current < state.questions.length-1) navQuestion(1); } }
function navQuestion(dir) { const next = state.current + dir; if (next < 0 || next >= state.questions.length) { if(next>=state.questions.length) confirmFinish(); return; } state.current = next; renderQuestion(); }

// ── Timer & Finish ──
function startTimer() {
  clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    state.timerSeconds--;
    const el = document.getElementById('timer-display');
    el.textContent = `${Math.floor(state.timerSeconds/3600)}:${String(Math.floor((state.timerSeconds%3600)/60)).padStart(2,'0')}:${String(state.timerSeconds%60).padStart(2,'0')}`;
    if (state.timerSeconds < 300) el.classList.add('danger');
    if (state.timerSeconds <= 0) { clearInterval(state.timerInterval); finishExam(); }
  }, 1000);
}

function confirmFinish() {
  const unans = state.questions.length - Object.keys(state.answers).filter(k => state.answers[k] !== null).length;
  if (unans > 0 && !state.finished && !confirm(`Finish with ${unans} unanswered questions?`)) return;
  finishExam();
}

async function finishExam() {
  clearInterval(state.timerInterval);
  state.finished = true;

  let correct = 0, wrong = 0, skipped = 0;
  const domMap = {};

  state.questions.forEach((q, i) => {
    const ans = state.answers[i];
    const d = q.domain;
    if (!domMap[d]) domMap[d] = { correct: 0, total: 0 };
    domMap[d].total++;
    
    // Update Global Heatmap stats
    if(!state.globalDomainStats[d]) state.globalDomainStats[d] = { total: 0, correct: 0 };
    state.globalDomainStats[d].total++;

    if (ans === null || ans === undefined) skipped++;
    else if (ans === q.answer) { correct++; domMap[d].correct++; state.globalDomainStats[d].correct++; }
    else wrong++;
  });

  await dbSet('pca:domain-mastery', state.globalDomainStats); // Save heatmap data

  const scorePct = Math.round((correct / state.questions.length) * 100);
  document.getElementById('score-circle').className = 'score-circle' + (scorePct >= 72 ? ' pass' : '');
  document.getElementById('score-pct').textContent = scorePct + '%';
  document.getElementById('result-title').textContent = scorePct >= 72 ? '🎉 PASS!' : '📚 Keep Studying!';
  document.getElementById('r-correct').textContent = correct; document.getElementById('r-wrong').textContent = wrong; document.getElementById('r-skipped').textContent = skipped;

  document.getElementById('domain-chart').innerHTML = '<h3>Session Breakdown</h3>' + Object.entries(domMap).map(([d, s]) => {
    const pct = Math.round((s.correct / s.total) * 100);
    return `<div class="db-row"><span class="db-label">${d}</span><div class="db-bar-wrap"><div class="db-bar" style="width:${pct}%;background:${pct>=80?'var(--green)':pct>=60?'var(--yellow)':'var(--red)'}"></div></div><span class="db-score">${s.correct}/${s.total}</span></div>`;
  }).join('');

  await saveSession(scorePct, state.questions.length, state.answers, state.questions);
  showScreen('screen-results');
}

// ── Review & AI Tutor ──
async function goReview() {
  const list = document.getElementById('review-list');
  list.innerHTML = state.questions.map((q, i) => {
    const userAns = state.answers[i];
    const ok = userAns === q.answer;
    const stat = userAns == null ? 'SKIPPED' : ok ? 'CORRECT' : 'WRONG';
    
    // Build AI Tutor button for wrong answers
    const tutorBtn = (!ok && userAns != null) ? 
      `<button class="btn-tutor" onclick="askTutor(${i}, '${q.opts[userAns].replace(/'/g,"")}', '${q.opts[q.answer].replace(/'/g,"")}')">🤖 Ask AI Tutor: Why is this wrong?</button>
       <div id="tutor-box-${i}" class="ai-tutor-box"></div>` : '';

    return `<div class="review-q">
      <div class="q-num"><span>Q${i+1} · ${q.domain}</span><span class="pill ${ok?'ok':userAns==null?'skip':'bad'}">${stat}</span></div>
      <div class="q-txt">${q.text}</div>
      <div style="font-size:13px; margin-top:8px;">
        <div style="color:var(--muted)">Your answer: <span style="color:${ok?'var(--green)':'var(--red)'}">${userAns!=null ? q.opts[userAns] : 'None'}</span></div>
        ${!ok ? `<div style="color:var(--muted);margin-top:4px;">Correct: <span style="color:var(--green)">${q.opts[q.answer]}</span></div>` : ''}
        ${tutorBtn}
      </div>
    </div>`;
  }).join('');
  showScreen('screen-review');
}

async function askTutor(qIndex, wrongText, correctText) {
  const box = document.getElementById(`tutor-box-${qIndex}`);
  box.classList.add('visible');
  box.innerHTML = `<div class="spinner" style="width:12px;height:12px;border-color:var(--accent);border-top-color:transparent;display:inline-block;margin-right:8px"></div> <em>AI Tutor is analyzing your answer...</em>`;
  
  try {
    const res = await fetch('/api/tutor', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ question: state.questions[qIndex].text, correct: correctText, wrong: wrongText })
    });
    const data = await res.json();
    box.innerHTML = `<strong>🤖 AI Tutor Analysis</strong>${data.text}`;
  } catch (e) { box.innerHTML = `⚠️ Could not reach AI Tutor.`; }
}

// ── Adaptive AI Generation ──
async function startAdaptiveSession() {
  const banner = document.getElementById('home-ai-banner');
  const msg = document.getElementById('home-ai-banner-msg');
  banner.style.display = 'flex';
  msg.textContent = 'Analyzing weaknesses...';

  // 1. Identify Weak Domains
  const domStats = state.globalDomainStats;
  let weak = [];
  let totalPct = 0; let totalSessions = 0;
  
  for (let [d, data] of Object.entries(domStats)) {
    if (data.total >= 3) {
      let pct = data.correct / data.total;
      totalPct += pct; totalSessions++;
      if (pct < 0.65) weak.push(d); // Threshold for weakness
    }
  }

  // Fallback if no history
  if (weak.length === 0) weak = ['Designing & Planning', 'Security & Compliance']; 
  const avg = totalSessions > 0 ? totalPct / totalSessions : 0.5;
  const diff = avg > 0.75 ? 'hard' : avg < 0.5 ? 'easy' : 'medium';

  msg.textContent = `Generating adaptive questions focused on: ${weak.slice(0,2).join(', ')} (Difficulty: ${diff.toUpperCase()})...`;

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weakDomains: weak, difficulty: diff })
    });
    
    if (!res.ok) throw new Error("API failed");
    const rawTxt = (await res.json()).text;
    
    // Parse JSON
    let text = rawTxt.replace(/^```json\s*/im, '').replace(/\s*```\s*$/im, '').trim();
    const parsed = JSON.parse(text.slice(text.indexOf('[')));
    
    if (parsed.length > 0) {
      const existing = await dbGet('pca:ai-questions') || [];
      await dbSet('pca:ai-questions', [...existing, ...parsed]);
      
      // Instantly start exam with these specific new questions
      state.mode = 'exam';
      state.questions = parsed;
      banner.style.display = 'none';
      initExamUI();
      return;
    }
  } catch (err) { console.error(err); }

  msg.textContent = "⚠️ Failed to generate adaptive session. Try standard mode.";
  setTimeout(() => banner.style.display = 'none', 3000);
}

// ── Base Nav ──
function showScreen(id) { document.querySelectorAll('.screen').forEach(s => s.classList.remove('active')); document.getElementById(id).classList.add('active'); }
function goHome() { clearInterval(state.timerInterval); renderDashboard(); showScreen('screen-home'); }
function showToast(msg) { const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 3000); }
function confirmGoHome() { if(Object.keys(state.answers).length > 0 && !state.finished && !confirm('Quit? Progress lost.')) return; goHome(); }