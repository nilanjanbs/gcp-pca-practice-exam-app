# GCP PCA Mock Exam · Adaptive Learning

A single-page Node.js + vanilla-JS web app that helps you prepare for the **Google Cloud Professional Cloud Architect (PCA)** exam with an exam-grade question bank, AI-powered remediation, and adaptive sprints that target your weakest domains.

The project ships with **70+ expert-written scenario questions** across all six PCA blueprint domains (medium / hard / challenging difficulty) and a swappable AI backend that works with **Anthropic Claude**, **Google Gemini**, or **OpenAI ChatGPT** — pick whichever you prefer in `.env` and the rest of the app is unchanged.

You can also generate **unlimited additional questions** through the built-in Admin UI using your own API key. No vendor lock-in, no signup, runs entirely on your laptop.

---

## What this project is

A self-contained training tool for the GCP PCA exam, with two halves:

1. A **frontend** (`/public`) that delivers the practice experience: timed mock exams, formative practice mode, adaptive AI sprints, flagging, spaced repetition, domain-mastery heatmap, concept-level analytics, and a "Save for Later" review panel.
2. A **backend** (`server.js`) that proxies to one of three AI providers for adaptive question generation, remediation briefs, and per-question tutor explanations — and persists state to a local `database.json` file (no external database required).

It is designed for **personal use** — clone, run locally, study. There is no auth, no telemetry, no cloud dependency.

---

## Features

### Practice modes

- **Timed Mock Exam** — 50-question full-length exam with a real timer, pacing pill, and a Save-for-Later panel that lets you flag questions and jump back to them mid-test.
- **Practice Mode** — untimed, with confidence tracking ("I'm sure" / "I'm guessing") so the spaced-repetition engine learns when you're guessing right.
- **Adaptive AI Sprint** — generates a fresh micro-set of 5–10 questions targeted at your weakest concepts. Shows a transparency panel before spending the API call so you know what the AI will focus on.
- **Flagged Review** — runs a session containing only questions you've previously flagged.

### Scoring & analytics

- **Domain Mastery Heatmap** with confidence-aware tiers (small samples render gray, not red — so you don't get punished for trying once).
- **Top Missed Concepts** panel showing per-concept mastery once you've seen each concept twice.
- **Session History** with score, status, and weakest domain per session.
- Both heatmap and concept panel are collapsible (M3-style smooth slide).

### AI-powered learning

- **Adaptive question generation** targeting your specific failed concepts, not generic prompts.
- **Remediation briefs** after each session — bullet-pointed Markdown explainers of the principles you missed.
- **AI Tutor** on individual wrong answers — a tight "why your choice is wrong / why this is right" explanation.
- All three providers (Claude / Gemini / ChatGPT) produce the same output schema, so swapping providers requires no code changes.

### Question content

- **70+ in-built questions** spanning Designing & Planning, Managing & Provisioning, Security & Compliance, Analyzing & Optimizing, Managing Implementation, and Reliability & Operations.
- Three difficulty tiers: `medium`, `hard`, **`challenging`** (highest, scenario-heavy with very close distractors).
- Includes 20 case-study questions tied to the official PCA case studies (EHR Healthcare, Helicopter Racing League, Mountkirk Games, TerramEarth) and 20 brand-new most-challenging scenarios on contemporary 2026 topics (BigQuery Omni, AlloyDB columnar, NCC hub-and-spoke, Eventarc Advanced, Cloud Workstations, Apigee Hybrid, Cloud DNS routing policies, Datastream CDC, etc.).
- Every question includes a 4-option MC, the correct index, a detailed explanation, and a suggested "Targeted Search" hint to deepen study.

### UX & polish

- Material 3 design language with Google-Cloud-inspired tonal palette.
- Light + dark mode auto-detected (toggle in header).
- Keyboard shortcuts in exam mode.
- Markdown + Mermaid diagram rendering inside questions and explanations.
- Inline flag button on every question; saved flags persist across sessions.
- First-run onboarding walkthrough.

### Admin & data

- **Admin & Analytics Dashboard** with session history, manual AI-fetch override (force-fetch a fresh batch of 10 targeted questions), and difficulty / domain summaries.
- All state lives in `database.json` — easy to back up, share, or wipe.
- Backup folder under `_db_backups/` with timestamped snapshots.

---

## Tech stack

- **Runtime:** Node.js ≥ 18 (ES modules)
- **Server:** Express 4 (CORS, static, JSON middleware)
- **AI SDKs:** `@anthropic-ai/sdk`, `@google/generative-ai`, `openai` — all loaded at boot, only the selected provider is called per request
- **Storage:** local `database.json` (read/written by the `/api/db/:key` endpoints)
- **Frontend:** vanilla JavaScript, semantic HTML, hand-written CSS with Material 3 tokens

No build step. No bundler. Nothing transpiled. Edit the file, hit reload.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-fork>/gcp-pca-mock-app.git
cd gcp-pca-mock-app

# 2. Install
npm install

# 3. Configure your provider + key (see next section)
cp .env.example .env   # if you maintain an example file
$EDITOR .env

# 4. Run
./start.sh             # runs in background, logs to server.log
# or:
npm start              # foreground

# 5. Open
open http://localhost:4000
```

To stop the background server: `./stop.sh`.

---

## Configuration: switching AI provider in `.env`

The whole app speaks to **one** AI provider at a time. The provider is chosen at startup by the `AI_PROVIDER` variable in `.env`. To switch from Claude to Gemini to ChatGPT, you only edit `.env` and restart the server — no code changes.

### `.env` template

```ini
# ── Server ──
PORT=4000

# ── AI Provider Selection ──
# Pick exactly one of: claude  |  gemini  |  openai
AI_PROVIDER=claude

# ── API keys (only the one matching AI_PROVIDER is required) ──
ANTHROPIC_API_KEY=sk-ant-...your-claude-key...
GEMINI_API_KEY=AIza...your-gemini-key...
OPENAI_API_KEY=sk-...your-openai-key...
```

### Steps to switch

1. **Open** the `.env` file in the project root.
2. **Set `AI_PROVIDER`** to one of the three values:

   | You want to use | Set `AI_PROVIDER` to | Get a key from |
   |---|---|---|
   | Anthropic **Claude** | `claude` | <https://console.anthropic.com/> |
   | Google **Gemini** | `gemini` | <https://aistudio.google.com/app/apikey> |
   | OpenAI **ChatGPT (GPT-4o)** | `openai` | <https://platform.openai.com/api-keys> |

3. **Paste the matching API key** into the corresponding `*_API_KEY` line. Keys for the providers you're not using can stay as placeholders — they're never read.
4. **Restart the server**:

   ```bash
   ./stop.sh && ./start.sh
   ```

5. The server logs the active provider on each AI call, e.g. `🤖 Requesting from: claude`. If you see the wrong provider, double-check your `.env`.


---

## Question pool: 120+ in-built, plus your own via Admin UI

The shipping `database.json` contains **70 expert-written PCA scenario questions** under the `pca:seed-questions` key. They cover every PCA blueprint domain at medium / hard / challenging difficulty.

**You are free to generate more questions inside the app at any time using your own API key.**

### Adding questions through the Admin UI

1. Open the app at `http://localhost:4000`.
2. From the home screen, click **"Open Admin & Analytics Dashboard"** at the bottom.
3. In the **"Manual AI Generation Override"** panel:
   - (Optionally) tick **"Include detailed AI Tutor explanations for each new question"**.
   - Click **"Fetch New Questions Now"** — the server uses **your** API key (from `.env`) and the active provider to generate a fresh batch of 10 questions targeted at your historical weak areas.
4. The new questions are persisted under `pca:ai-questions` in `database.json` and become available in Practice / Adaptive Sprint sessions.

Because the same prompt template is used regardless of provider, a Gemini-generated question is structurally identical to a Claude-generated one. Switch providers anytime; previously-generated questions stay valid.

### Adaptive Sprint (in-session)

From the home screen's **"AI Adaptive Sprint"** mode card, you can also generate a smaller, on-demand sprint that targets specific failing concepts. The transparency panel shows you which weak areas the sprint will focus on before you spend the API call.

### Bring-your-own-questions

If you'd rather hand-author questions, edit `database.json` directly. Each item under `pca:seed-questions` is shaped:

```jsonc
{
  "id": "q071",
  "domain": "Designing & Planning",
  "diff": "challenging",
  "text": "Scenario...",
  "opts": ["A", "B", "C", "D"],
  "answer": 0,                    // 0-indexed correct option
  "explanation": "Why A is right...\n\n🔍 Targeted Search: '...', '...'."
}
```

Optional fields used by AI-generated questions: `concepts: string[]`, `learning_objective: string`.

---

## Project structure

```
gcp-pca-mock-app/
├── server.js              # Express server + AI adapter (Claude / Gemini / OpenAI)
├── package.json
├── .env                   # AI_PROVIDER + API keys (gitignored)
├── start.sh / stop.sh     # background-process helpers
├── database.json          # 70+ questions + per-user state (sessions, flags, mastery)
├── _db_backups/           # timestamped DB snapshots
└── public/
    ├── index.html         # SPA shell — home, exam, results, admin, modals
    ├── styles.css         # Material 3 design system, light+dark
    ├── app.js             # session state machine, rendering, navigation
    └── features.js        # flag system, concept analytics, collapsibles, onboarding
```

---

## Development notes

- The frontend is intentionally framework-free. State lives in a single `state` object inside `app.js`. Persistent state is namespaced under `pca:*` keys via `dbGet` / `dbSet` (small wrappers over `/api/db/:key`).
- The backend has only three AI endpoints (`/api/generate`, `/api/brief`, `/api/tutor`) plus the generic key-value DB endpoints. All of them route through the unified `generateAIResponse(prompt)` adapter.
- **Logs:** `server.log` (when started via `./start.sh`).
- **Process:** `server.pid` records the background PID for `./stop.sh`.

---

## Troubleshooting

- **`MISSING_KEY` errors** — your `.env` doesn't have a key for the provider you selected with `AI_PROVIDER`. Either paste a real key or change `AI_PROVIDER`.
- **`429 Rate Limit`** — your selected provider is throttling. Wait 60s, or temporarily switch `AI_PROVIDER` to a different vendor in `.env` and restart.
- **Port already in use** — change `PORT` in `.env`.
- **Wiping all your progress** — replace `database.json` with one from `_db_backups/`, or copy any seed-only backup (e.g. `database.20260425-185106.json`).

---

## Contributing

Pull requests welcome. The codebase is small and intentionally hackable. Areas that are easy to extend:

- New question batches (just append under `pca:seed-questions`).
- New AI provider — add a case to the switch in `generateAIResponse()` and wire its SDK.
- New analytics widgets — drop a new section into `index.html` and its renderer into `features.js`.

---

## License

This project is provided as-is for personal exam preparation. The bundled questions are original works written for this app and are licensed for personal study use. The Google Cloud Professional Cloud Architect exam, GCP product names, and case-study names are trademarks of Google LLC and are referenced here under nominative fair use; this project is **not** affiliated with or endorsed by Google.
