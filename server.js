import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// SDKs
import { GoogleGenerativeAI } from '@google/generative-ai';
import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;
const DB_FILE = path.join(__dirname, 'database.json');

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// ── AI Provider Clients ──
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "MISSING_KEY");
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY || "MISSING_KEY"});
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY || "MISSING_KEY"});

if (!fs.existsSync(DB_FILE)) {
  fs.writeFileSync(DB_FILE, JSON.stringify({}));
}

/**
 * ── Unified AI Adapter ──
 * This central function handles the switching between providers.
 */
async function generateAIResponse(prompt) {
  const provider = process.env.AI_PROVIDER || 'gemini';
  console.log(`🤖 Requesting from: ${provider}`);

  try {
    switch (provider.toLowerCase()) {
      case 'claude':
        const clResponse = await anthropic.messages.create({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 4000,
          messages: [{ role: "user", content: prompt }],
        });
        return clResponse.content[0].text;

      case 'openai':
        const oaResponse = await openai.chat.completions.create({
          model: "gpt-4o",
          messages: [{ role: "user", content: prompt }],
        });
        return oaResponse.choices[0].message.content;

      case 'gemini':
      default:
        const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
        const result = await model.generateContent(prompt);
        return (await result.response).text();
    }
  } catch (error) {
    console.error(`❌ ${provider.toUpperCase()} API Error:`, error.message);
    throw error;
  }
}

// ── 1. Targeted Adaptive AI Generation ──
app.post('/api/generate', async (req, res) => {
  try {
    const { type, targets, prompt: legacyPrompt } = req.body;
    let finalPrompt;

    if (legacyPrompt) {
      finalPrompt = legacyPrompt;
    } else if ((type === 'adaptive' || type === 'daily_review') && Array.isArray(targets) && targets.length > 0) {
      const targetConcepts = targets.map(t => `Domain: ${t.domain}, Concept from missed question: "${t.text}"`).join(' | ');
      finalPrompt = `You are a GCP Professional Cloud Architect exam setter.
The student recently failed questions regarding these specific sub-concepts: ${targetConcepts}.
Generate exactly 5 NEW, highly complex scenario-based questions that test the EXACT SAME underlying architectural principles, but using completely different scenarios.
Add a "learning_objective" field briefly stating what specific concept this targets.

You MAY use Markdown in the "text" and "explanation" fields:
- **bold** for key product names (e.g., **Cloud SQL**, **BigQuery**).
- Fenced code blocks with language tags for YAML / JSON / gcloud commands.
- GitHub-flavored tables to compare options where relevant.
- A fenced \`\`\`mermaid block to embed an architecture diagram (flowchart TD or LR) when the scenario genuinely benefits from one.

STRICT OUTPUT: Return ONLY a raw JSON array. Escape newlines inside strings as \\n.
Format: [{ "id": "ai-adapt-...", "domain": "...", "diff": "hard", "learning_objective": "...", "text": "...", "opts": ["A","B","C","D"], "answer": 0, "explanation": "..." }]`;
    } else {
      finalPrompt = `You are a GCP PCA exam setter. Generate 5 scenario-based multiple-choice questions focusing on varied PCA domains.
You MAY use Markdown in "text" and "explanation" (bold, code fences, tables, and optional \`\`\`mermaid diagrams).
STRICT OUTPUT: Return ONLY a raw JSON array.
Format: [{ "id": "ai-std-...", "domain": "...", "diff": "medium", "learning_objective": "General Practice", "text": "...", "opts": ["A","B","C","D"], "answer": 0, "explanation": "..." }]`;
    }

    const responseText = await generateAIResponse(finalPrompt);
    res.json({ text: responseText });
  } catch (error) {
    if (error.status === 429) {
      return res.status(429).json({ error: "Rate Limit Exceeded", details: "AI provider is busy. Wait 60s." });
    }
    res.status(500).json({ error: "Failed to generate AI questions", details: error.message });
  }
});

// ── 2. Remediation Brief (The "Teach" Phase) ──
app.post('/api/brief', async (req, res) => {
  try {
    const { topics } = req.body;
    if (!topics || !Array.isArray(topics)) throw new Error("Missing topics array");
    
    const prompt = `A GCP PCA student just failed questions on these specific topics: ${topics.join(' | ')}.
    Write a highly concise, 3-bullet-point "Remediation Brief" explaining the core GCP architectural principles. 
    Format as clean HTML (use <ul>, <li>, <strong>).`;

    const htmlContent = await generateAIResponse(prompt);
    res.json({ html: htmlContent.replace(/```html|```/g, '') });
  } catch (error) {
    res.status(500).json({ html: "<p>Unable to load remediation brief at this time.</p>" });
  }
});

// ── 3. AI Tutor (Why wrong) ──
app.post('/api/tutor', async (req, res) => {
  try {
    const { question, correct, wrong } = req.body;
    const prompt = `Student got a GCP PCA question wrong.
    Q: "${question}"
    Their choice: "${wrong}"
    Correct answer: "${correct}"
    In 3 concise sentences: 1. Why their choice is wrong. 2. Why the right choice is correct. Plain text only.`;

    const tutorText = await generateAIResponse(prompt);
    res.json({ text: tutorText });
  } catch (error) { 
    res.status(500).json({ error: "Tutor unavailable right now." }); 
  }
});

// ── Local JSON DB Endpoints ──
app.get('/api/db/:key', (req, res) => {
  try {
    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    res.json({ value: db[req.params.key] !== undefined ? db[req.params.key] : null });
  } catch (err) { res.status(500).json({ error: "DB read error" }); }
});

app.post('/api/db/:key', (req, res) => {
  try {
    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    db[req.params.key] = req.body.value;
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
    res.json({ success: true });
  } catch (err) { res.status(500).json({ error: "DB write error" }); }
});

app.listen(port, () => console.log(`Server running at http://localhost:${port}`));