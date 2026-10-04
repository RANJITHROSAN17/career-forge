/**
 * Career Forge — AI Resume & Job Match Studio (Anna App Bundle Controller)
 *
 * Connects to Anna via the runtime SDK loaded from:
 *   /static/anna-apps/_sdk/latest/index.js
 *
 * Host API methods used (all declared in manifest.json#ui.host_api):
 *   anna.tools.invoke({ tool_id, method: "career", args: { action, ... } })
 *   anna.storage.get({ key })
 *   anna.storage.set({ key, value })
 *   anna.chat.write_message({ role, content })
 *   anna.chat.append_artifact({ title, content, type })
 *   anna.window.set_title({ title })
 */

import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const DEV_FALLBACK_TOOL_ID = "tool-test-career-engine-12345678";
const TOOL_ID =
  (typeof window !== "undefined" &&
    window.__ANNA_TOOL_IDS__ &&
    window.__ANNA_TOOL_IDS__["career-engine"]) ||
  DEV_FALLBACK_TOOL_ID;
const TOOL_METHOD = "career";
const STORAGE_DRAFT_KEY = "career-forge:draft-v1";

const PRESETS = {
  "ai-engineer": {
    role: "Senior Full-Stack AI Engineer",
    company: "Anna Labs",
    resume: `Alex Rivera | alex.rivera@devmail.io | https://github.com/alexrivera | https://linkedin.com/in/alexrivera

SUMMARY
Full-Stack & AI Engineer with 4+ years building LLM applications, Python microservices, and interactive web platforms.

SKILLS
Python, TypeScript, JavaScript, FastAPI, React, Next.js, PostgreSQL, Docker, LLM Agents, Prompt Engineering, Git

EXPERIENCE
Senior Software Engineer — CloudScale AI (2024–Present)
• Architected Python and FastAPI inference microservices handling 85,000+ daily requests with 99.95% uptime.
• Worked on multi-step LLM Agents and tool-calling workflows for automated customer triage.
• Built React and TypeScript analytics dashboards used by 1,200+ enterprise operators.
• Helped with PostgreSQL query tuning and Docker container deployments across staging and production.`,
    jd: `Role: Senior Full-Stack AI Engineer — Anna Labs
We are looking for a Senior Full-Stack AI Engineer to architect and ship production AI Agents, MCP / Tool Calling plugins, and RAG & Vector DB pipelines.

Key Requirements:
• Deep fluency in Python, TypeScript, FastAPI, and React / Next.js.
• Hands-on production experience building LLM Agents, RAG & Vector DB systems (pgvector, Pinecone, or Qdrant), and LangChain / LlamaIndex workflows.
• Experience with Model Context Protocol (MCP), JSON-RPC tool calling, and Prompt Engineering evals.
• Strong Cloud & DevOps foundation: AWS, Docker, Kubernetes, CI/CD (GitHub Actions), and Observability (Prometheus, OpenTelemetry).
• Proven track record of technical mentorship and shipping low-latency distributed systems.`,
  },
  "data-scientist": {
    role: "Staff Machine Learning & Data Scientist",
    company: "QuantPulse AI",
    resume: `Priya Sharma | priya.sharma@mlhub.io | https://github.com/priyasharma-ml

SUMMARY
Machine Learning Scientist specializing in predictive modeling, NLP transformers, and large-scale data pipelines.

SKILLS
Python, SQL, PyTorch, TensorFlow, Scikit-learn, Pandas, Spark, Airflow, AWS, Experimentation

EXPERIENCE
Lead Data Scientist — FinSight Analytics (2023–Present)
• Engineered PyTorch ranking models that increased recommendation click-through rate by 19% across 3M+ monthly active users.
• Responsible for building Spark and Airflow ETL data pipelines processing 4TB of daily event logs.
• Assisted in A/B testing and statistical experimentation frameworks for checkout conversion.
• Trained custom NLP classifiers and deployed inference endpoints on AWS EC2.`,
    jd: `Role: Staff Machine Learning & Data Scientist
Join QuantPulse AI to lead our next-generation foundation model fine-tuning, RAG retrieval, and real-time ML experimentation platform.

Requirements:
• Expert in Python, SQL (Snowflake/BigQuery), PyTorch, and Fine-Tuning & RLHF (LoRA, QLoRA, HuggingFace Transformers).
• Production experience with RAG & Vector DB architectures, LLM Agents, and Prompt Engineering evaluation benchmarks.
• Strong command of Data Pipelines (Spark, Airflow, Kafka, dbt) and A/B Testing & Experimentation.
• Cloud & MLOps deployment using AWS (SageMaker/Bedrock), Docker, Kubernetes, and CI/CD automation.
• Track record of technical mentorship and cross-functional stakeholder alignment.`,
  },
  "product-manager": {
    role: "Senior AI Product Manager",
    company: "Nexus Workflow OS",
    resume: `Jordan Lee | jordan.lee@pmcraft.io | https://linkedin.com/in/jordanlee-pm

SUMMARY
Product Manager with 5 years scaling B2B SaaS and AI workflow products from 0 to 50K+ MAU.

SKILLS
Product Strategy & Roadmap, Agile & Scrum, User Research, Mixpanel, SQL, Prompt Engineering, A/B Testing

EXPERIENCE
Product Manager — FlowStack SaaS (2023–Present)
• Spearheaded launch of an AI copilot assistant, growing adoption to 18,500 MAU within 90 days and lifting D30 retention by 14%.
• Worked on product roadmap, PRDs, and sprint execution across a cross-functional team of 9 engineers and designers.
• Conducted 60+ user research interviews and funnel cohort analyses in Mixpanel and SQL.
• Helped with go-to-market pricing experiments that expanded self-serve ARR by $420K.`,
    jd: `Role: Senior AI Product Manager — Nexus Workflow OS
We need a technical AI Product Manager to own our Agentic App Store, developer SDK experience, and MAU growth loops.

Requirements:
• Proven experience owning Product Strategy & Roadmap, PRDs, and GTM launches for AI or developer platforms.
• Deep familiarity with LLM Agents, Prompt Engineering, RAG & Vector DB concepts, and MCP / Tool Calling ecosystems.
• Data-driven mindset: SQL, User Research & Analytics (Amplitude/Mixpanel, funnel retention, MAU growth), and A/B Testing & Experimentation.
• Strong Agile & Cross-Functional leadership working closely with Python and TypeScript engineering teams.`,
  },
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const els = {
  roleInput: $("#role-input"),
  companyInput: $("#company-input"),
  resumeInput: $("#resume-input"),
  jdInput: $("#jd-input"),
  wordCountLabel: $("#word-count-label"),
  bulletCountLabel: $("#resume-bullet-count"),
  scanBtn: $("#scan-btn"),
  quickRewriteBtn: $("#quick-rewrite-btn"),
  clearInputsBtn: $("#clear-inputs-btn"),
  clearHistoryBtn: $("#clear-history-btn"),
  historyList: $("#history-list"),
  statScans: $("#stat-scans"),
  statBest: $("#stat-best"),
  statAvg: $("#stat-avg"),
  connDot: $("#conn-dot"),
  connLabel: $("#conn-label"),
  themeToggle: $("#theme-toggle"),
  statusBanner: $("#status-banner"),
  statusText: $("#status-text"),
  gaugeFill: $("#gauge-fill"),
  overallScoreVal: $("#overall-score-val"),
  verdictPill: $("#verdict-pill"),
  activeRoleTag: $("#active-role-tag"),
  subTechVal: $("#sub-tech-val"),
  subTechBar: $("#sub-tech-bar"),
  subKwVal: $("#sub-kw-val"),
  subKwBar: $("#sub-kw-bar"),
  subQuantVal: $("#sub-quant-val"),
  subQuantBar: $("#sub-quant-bar"),
  subAtsVal: $("#sub-ats-val"),
  subAtsBar: $("#sub-ats-bar"),
  priorityList: $("#priority-list"),
  matchedCountBadge: $("#matched-count-badge"),
  matchedChips: $("#matched-chips"),
  missingCountBadge: $("#missing-count-badge"),
  missingList: $("#missing-list"),
  checksGrid: $("#checks-grid"),
  runBulletsBtn: $("#run-bullets-btn"),
  copyAllBulletsBtn: $("#copy-all-bullets-btn"),
  bulletsList: $("#bullets-list"),
  coverToneSelect: $("#cover-tone-select"),
  runCoverBtn: $("#run-cover-btn"),
  coverOutput: $("#cover-output"),
  runInterviewBtn: $("#run-interview-btn"),
  interviewList: $("#interview-list"),
  pinArtifactBtn: $("#pin-artifact-btn"),
  askCoachBtn: $("#ask-coach-btn"),
  presetChips: $$(".preset-chip[data-preset]"),
  tabBtns: $$(".tab-btn[data-tab]"),
};

const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 58; // r=58 => 364.42

let anna = null;
let currentScan = null;
let latestBulletsCopyText = "";
let isBusy = false;

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

async function init() {
  bindEvents();
  loadPreset("ai-engineer", false);

  try {
    anna = await AnnaAppRuntime.connect();
    setConnectionStatus(true, "Anna Runtime Connected");
  } catch (err) {
    setConnectionStatus(false, "Preview Mode");
    console.warn("[career-forge] running in standalone preview:", err?.message || err);
  }

  // Restore saved draft from Anna Storage if present
  if (anna) {
    try {
      const saved = await anna.storage.get({ key: STORAGE_DRAFT_KEY });
      const draft = saved?.value || saved?.result?.value;
      if (draft && typeof draft === "object" && draft.resume) {
        els.roleInput.value = draft.role || els.roleInput.value;
        els.companyInput.value = draft.company || els.companyInput.value;
        els.resumeInput.value = draft.resume;
        els.jdInput.value = draft.jd || els.jdInput.value;
        updateInputCounters();
      }
    } catch {
      /* storage optional on first boot */
    }
  }

  // Fetch initial state or trigger initial scan so user sees immediate value
  await refreshStateOrAutoScan();
}

function bindEvents() {
  els.themeToggle.addEventListener("click", () => {
    const next = document.body.dataset.theme === "light" ? "dark" : "light";
    document.body.dataset.theme = next;
  });

  els.presetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = chip.dataset.preset;
      els.presetChips.forEach((c) => c.classList.toggle("is-active", c === chip));
      loadPreset(key, true);
    });
  });

  els.clearInputsBtn.addEventListener("click", () => {
    els.presetChips.forEach((c) => c.classList.remove("is-active"));
    els.roleInput.value = "";
    els.companyInput.value = "";
    els.resumeInput.value = "";
    els.jdInput.value = "";
    updateInputCounters();
    els.resumeInput.focus();
  });

  [els.roleInput, els.companyInput, els.resumeInput, els.jdInput].forEach((inp) => {
    inp.addEventListener("input", () => {
      updateInputCounters();
      persistDraft();
    });
  });

  els.tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  els.scanBtn.addEventListener("click", () => runScan());
  els.quickRewriteBtn.addEventListener("click", async () => {
    switchTab("bullets");
    await runBulletRewrites();
  });

  els.runBulletsBtn.addEventListener("click", () => runBulletRewrites());
  els.copyAllBulletsBtn.addEventListener("click", () => {
    if (!latestBulletsCopyText) {
      showStatus("Generate bullet rewrites first.", "error");
      return;
    }
    copyText(latestBulletsCopyText, "Copied all upgraded XYZ bullets!");
  });

  els.runCoverBtn.addEventListener("click", () => runCoverLetter());
  els.runInterviewBtn.addEventListener("click", () => runInterviewPrep());
  els.clearHistoryBtn.addEventListener("click", () => clearHistory());
  els.askCoachBtn.addEventListener("click", () => askCoachInChat());
  els.pinArtifactBtn.addEventListener("click", () => pinScanArtifact());
}

function loadPreset(key, autoRun = false) {
  const p = PRESETS[key];
  if (!p) return;
  els.roleInput.value = p.role;
  els.companyInput.value = p.company;
  els.resumeInput.value = p.resume;
  els.jdInput.value = p.jd;
  updateInputCounters();
  if (autoRun) {
    runScan();
  }
}

function updateInputCounters() {
  const resText = els.resumeInput.value.trim();
  const words = resText ? resText.split(/\s+/).length : 0;
  const lines = resText
    .split(/\n+/)
    .map((l) => l.trim())
    .filter((l) => l.length >= 35).length;
  els.wordCountLabel.textContent = `${words} words`;
  els.bulletCountLabel.textContent = `${lines} experience lines`;
}

let draftTimer = null;
function persistDraft() {
  if (!anna) return;
  clearTimeout(draftTimer);
  draftTimer = setTimeout(async () => {
    try {
      await anna.storage.set({
        key: STORAGE_DRAFT_KEY,
        value: {
          role: els.roleInput.value,
          company: els.companyInput.value,
          resume: els.resumeInput.value,
          jd: els.jdInput.value,
        },
      });
    } catch {
      /* ignore */
    }
  }, 600);
}

// ---------------------------------------------------------------------------
// RPC Dispatcher Helper
// ---------------------------------------------------------------------------

function unwrapToolPayload(raw) {
  if (!raw) return null;
  // Handle AnnaAppRuntime shapes: { ok: true, result: { success: true, data: ... } } or { data: ... } or direct
  const inner = raw.result !== undefined ? raw.result : raw;
  if (inner && inner.success === false) {
    throw new Error(inner.error || "Tool invocation failed");
  }
  if (inner && inner.data !== undefined) {
    return inner.data;
  }
  return inner;
}

async function callCareerEngine(action, extraArgs = {}) {
  if (!anna) {
    throw new Error("Anna Runtime not connected");
  }
  if (isBusy) return null;
  isBusy = true;
  setButtonsDisabled(true);
  try {
    const raw = await anna.tools.invoke({
      tool_id: TOOL_ID,
      method: TOOL_METHOD,
      args: { action, ...extraArgs },
    });
    return unwrapToolPayload(raw);
  } finally {
    isBusy = false;
    setButtonsDisabled(false);
  }
}

async function refreshStateOrAutoScan() {
  if (!anna) return;
  try {
    const state = await callCareerEngine("get_state");
    if (state && state.active_scan) {
      currentScan = state.active_scan;
      renderScanResult(state.active_scan);
      renderStatsAndHistory(state.stats, state.recent);
      renderBulletsFromScan(state.active_scan);
      return;
    }
  } catch {
    /* proceed to initial scan */
  }
  await runScan(true);
}

// ---------------------------------------------------------------------------
// Primary Actions
// ---------------------------------------------------------------------------

async function runScan(silent = false) {
  const resume_text = els.resumeInput.value.trim();
  const job_description = els.jdInput.value.trim();
  const role_title = els.roleInput.value.trim() || "Target Role";
  const company_name = els.companyInput.value.trim() || "Target Organization";

  if (!resume_text || !job_description) {
    showStatus("Please provide both your Resume and the Target Job Description.", "error");
    return;
  }

  if (!silent) showStatus("Running ATS Match & Keyword Gap Analysis…", "info");

  try {
    const data = await callCareerEngine("analyze", {
      resume_text,
      job_description,
      role_title,
      company_name,
    });
    if (!data || !data.scan) return;

    currentScan = data.scan;
    renderScanResult(data.scan);
    renderStatsAndHistory(data.stats, data.recent);
    renderBulletsFromScan(data.scan);

    if (anna) {
      try {
        await anna.window.set_title({
          title: `Career Forge · ${data.scan.overall_score}% Match (${role_title})`,
        });
      } catch {
        /* ignore */
      }
    }

    if (!silent) {
      showStatus(
        `Scan complete! ATS Match Score: ${data.scan.overall_score}% for ${role_title}.`,
        "success"
      );
    }
  } catch (err) {
    showStatus(`Scan error: ${err?.message || err}`, "error");
  }
}

async function runBulletRewrites() {
  const resume_text = els.resumeInput.value.trim();
  const job_description = els.jdInput.value.trim();
  if (!resume_text) {
    showStatus("Paste your resume first to optimize bullets.", "error");
    return;
  }
  showStatus("Generating Google XYZ formula bullet rewrites…", "info");
  try {
    const data = await callCareerEngine("rewrite_bullets", {
      resume_text,
      job_description,
    });
    if (!data) return;
    renderRewritesList(data.rewrites || [], data.copy_ready_block || "");
    showStatus("Upgraded XYZ resume bullets ready!", "success");
  } catch (err) {
    showStatus(`Bullet rewrite error: ${err?.message || err}`, "error");
  }
}

async function runCoverLetter() {
  const resume_text = els.resumeInput.value.trim();
  const job_description = els.jdInput.value.trim();
  const role_title = els.roleInput.value.trim() || "Target Role";
  const company_name = els.companyInput.value.trim() || "Hiring Team";
  const tone = els.coverToneSelect.value || "modern";

  if (!resume_text) {
    showStatus("Paste your resume first to generate a tailored cover letter.", "error");
    return;
  }
  showStatus("Crafting tailored cover letter & recruiter cold DM…", "info");
  try {
    const data = await callCareerEngine("cover_letter", {
      resume_text,
      job_description,
      role_title,
      company_name,
      tone,
    });
    if (!data) return;
    renderCoverLetter(data);
    showStatus("Tailored Cover Letter & LinkedIn DM generated!", "success");
  } catch (err) {
    showStatus(`Cover letter error: ${err?.message || err}`, "error");
  }
}

async function runInterviewPrep() {
  const resume_text = els.resumeInput.value.trim();
  const job_description = els.jdInput.value.trim();
  const role_title = els.roleInput.value.trim() || "Target Role";

  if (!resume_text) {
    showStatus("Paste your resume first to generate interview prep questions.", "error");
    return;
  }
  showStatus("Building role-specific STAR & technical interview deck…", "info");
  try {
    const data = await callCareerEngine("interview_prep", {
      resume_text,
      job_description,
      role_title,
    });
    if (!data) return;
    renderInterviewPrep(data);
    showStatus("5 targeted STAR interview questions generated!", "success");
  } catch (err) {
    showStatus(`Interview prep error: ${err?.message || err}`, "error");
  }
}

async function clearHistory() {
  try {
    const data = await callCareerEngine("clear_history");
    if (data) {
      renderStatsAndHistory(data.stats, data.recent);
      showStatus("Scan history cleared.", "info");
    }
  } catch (err) {
    showStatus(`Could not clear history: ${err?.message || err}`, "error");
  }
}

async function askCoachInChat() {
  if (!anna) {
    showStatus("Anna Chat is available when running inside Anna AI OS.", "info");
    return;
  }
  const score = currentScan ? `${currentScan.overall_score}%` : "unscanned";
  const role = els.roleInput.value.trim() || "my target role";
  const missing =
    currentScan?.missing_keywords?.slice(0, 4).map((m) => m.skill).join(", ") || "none";
  try {
    await anna.chat.write_message({
      role: "user",
      content: `[Career Forge] I just scored ${score} for ${role}. My top missing keywords are: ${missing}. Coach, how should I position my experience to pass the ATS and hiring manager screen?`,
    });
    showStatus("Sent scan context to Anna Career Coach in chat!", "success");
  } catch (err) {
    showStatus(`Chat message failed: ${err?.message || err}`, "error");
  }
}

async function pinScanArtifact() {
  if (!anna) return;
  if (!currentScan) {
    showStatus("Run an ATS scan first before pinning a summary card.", "error");
    return;
  }
  try {
    await anna.chat.append_artifact({
      title: `ATS Scan: ${currentScan.role_title} (${currentScan.overall_score}%)`,
      type: "markdown",
      content: [
        `### Career Forge ATS Report — ${currentScan.role_title}`,
        `- **Overall ATS Score:** ${currentScan.overall_score}% (${currentScan.verdict})`,
        `- **Matched Skills:** ${currentScan.matched_keywords.map((m) => m.skill).join(", ") || "None"}`,
        `- **Missing Skills:** ${currentScan.missing_keywords.map((m) => m.skill).join(", ") || "None"}`,
      ].join("\n"),
    });
    showStatus("Pinned ATS Summary Card to Anna chat!", "success");
  } catch (err) {
    showStatus(`Artifact pin notice: ${err?.message || err}`, "info");
  }
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderScanResult(scan) {
  const score = Math.max(0, Math.min(100, Number(scan.overall_score) || 0));
  els.overallScoreVal.textContent = `${score}%`;
  const offset = GAUGE_CIRCUMFERENCE * (1 - score / 100);
  els.gaugeFill.style.strokeDasharray = String(GAUGE_CIRCUMFERENCE);
  els.gaugeFill.style.strokeDashoffset = String(offset);

  els.verdictPill.textContent = scan.verdict || "Scan Complete";
  els.verdictPill.dataset.tier = scan.tier || "medium";
  els.activeRoleTag.textContent = `${scan.role_title} · ${scan.company_name || "Target"}`;

  const sub = scan.sub_scores || {};
  setSubbar(els.subTechVal, els.subTechBar, sub.technical_match || 0);
  setSubbar(els.subKwVal, els.subKwBar, sub.keyword_alignment || 0);
  setSubbar(els.subQuantVal, els.subQuantBar, sub.quantified_impact || 0);
  setSubbar(els.subAtsVal, els.subAtsBar, sub.ats_readiness || 0);

  // Priorities
  els.priorityList.innerHTML = "";
  (scan.top_priorities || []).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    els.priorityList.appendChild(li);
  });

  // Matched keywords
  const matched = scan.matched_keywords || [];
  els.matchedCountBadge.textContent = String(matched.length);
  els.matchedChips.innerHTML = "";
  if (!matched.length) {
    els.matchedChips.innerHTML = `<span class="empty-chip">No exact JD keyword matches yet</span>`;
  } else {
    matched.forEach((m) => {
      const chip = document.createElement("span");
      chip.className = "skill-chip";
      chip.innerHTML = `<strong>${escapeHtml(m.skill)}</strong> <small>×${m.resume_mentions}</small>`;
      els.matchedChips.appendChild(chip);
    });
  }

  // Missing keywords
  const missing = scan.missing_keywords || [];
  els.missingCountBadge.textContent = String(missing.length);
  els.missingList.innerHTML = "";
  if (!missing.length) {
    els.missingList.innerHTML = `<span class="empty-chip">100% of detected target keywords are covered!</span>`;
  } else {
    missing.forEach((m) => {
      const div = document.createElement("div");
      div.className = "missing-item";
      div.innerHTML = `
        <div class="missing-item__top">
          <span>${escapeHtml(m.skill)} <small class="muted">(${escapeHtml(m.category)})</small></span>
          <span class="badge ${m.priority === "High Priority" ? "badge--warn" : "badge--accent"}">${escapeHtml(m.priority)}</span>
        </div>
        <div class="missing-item__tip">${escapeHtml(m.placement_tip)}</div>
      `;
      els.missingList.appendChild(div);
    });
  }

  // Section checks
  els.checksGrid.innerHTML = "";
  (scan.section_checks || []).forEach((chk) => {
    const card = document.createElement("div");
    card.className = "check-item";
    card.innerHTML = `
      <strong>${chk.passed ? "✅" : "⚠️"} ${escapeHtml(chk.label)}</strong>
      <span class="muted">${escapeHtml(chk.detail)}</span>
    `;
    els.checksGrid.appendChild(card);
  });
}

function renderBulletsFromScan(scan) {
  const audits = scan?.bullet_audits || [];
  const copyBlock = audits.map((a) => `• ${a.xyz_rewrite}`).join("\n");
  renderRewritesList(audits, copyBlock);
}

function renderRewritesList(rewrites, copyBlock) {
  latestBulletsCopyText = copyBlock || rewrites.map((r) => `• ${r.xyz_rewrite}`).join("\n");
  els.bulletsList.innerHTML = "";
  if (!rewrites.length) {
    els.bulletsList.innerHTML = `<p class="empty-state">No experience bullets found to rewrite.</p>`;
    return;
  }

  rewrites.forEach((item) => {
    const card = document.createElement("div");
    card.className = "bullet-card";
    const issueBadges = (item.issues || []).length
      ? item.issues.map((i) => `<span class="badge badge--warn">${escapeHtml(i)}</span>`).join(" ")
      : `<span class="badge badge--success">Quantified &amp; Strong Opener</span>`;

    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
        <strong>Bullet #${item.index} <span class="badge badge--accent">+ Keyword: ${escapeHtml(item.suggested_keyword)}</span></strong>
        <div>${issueBadges}</div>
      </div>
      <div class="bullet-card__orig">Original: "${escapeHtml(item.original)}"</div>
      <div class="bullet-card__variant">
        <div>
          <strong style="color:#34d399;font-size:0.74rem;display:block;">⚡ XYZ Impact-Quantified Rewrite:</strong>
          <span>${escapeHtml(item.xyz_rewrite)}</span>
        </div>
        <button class="copy-mini-btn" type="button" data-copy="${escapeAttr(item.xyz_rewrite)}">Copy</button>
      </div>
      <div class="bullet-card__variant">
        <div>
          <strong style="color:#a5b4fc;font-size:0.74rem;display:block;">🎯 ATS Keyword-First Variant:</strong>
          <span>${escapeHtml(item.keyword_rewrite)}</span>
        </div>
        <button class="copy-mini-btn" type="button" data-copy="${escapeAttr(item.keyword_rewrite)}">Copy</button>
      </div>
    `;
    card.querySelectorAll(".copy-mini-btn").forEach((btn) => {
      btn.addEventListener("click", () => copyText(btn.dataset.copy, "Copied upgraded bullet!"));
    });
    els.bulletsList.appendChild(card);
  });
}

function renderCoverLetter(data) {
  els.coverOutput.innerHTML = `
    <div class="cover-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <strong>📧 Email Subject Line</strong>
        <button class="copy-mini-btn" type="button" data-copy="${escapeAttr(data.email_subject)}">Copy Subject</button>
      </div>
      <div class="cover-pre">${escapeHtml(data.email_subject)}</div>
    </div>

    <div class="cover-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <strong>📄 Tailored Cover Letter (${escapeHtml(data.tone)} tone)</strong>
        <button class="copy-mini-btn" type="button" data-copy="${escapeAttr(data.cover_letter)}">Copy Cover Letter</button>
      </div>
      <div class="cover-pre">${escapeHtml(data.cover_letter)}</div>
    </div>

    <div class="cover-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <strong>💬 LinkedIn / Recruiter Cold DM</strong>
        <button class="copy-mini-btn" type="button" data-copy="${escapeAttr(data.linkedin_dm)}">Copy DM</button>
      </div>
      <div class="cover-pre">${escapeHtml(data.linkedin_dm)}</div>
    </div>
  `;

  els.coverOutput.querySelectorAll(".copy-mini-btn").forEach((btn) => {
    btn.addEventListener("click", () => copyText(btn.dataset.copy, "Copied to clipboard!"));
  });
}

function renderInterviewPrep(data) {
  const questions = data.questions || [];
  els.interviewList.innerHTML = "";
  questions.forEach((q) => {
    const card = document.createElement("div");
    card.className = "qa-card";
    const sg = q.star_guide || {};
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <span class="badge badge--accent">Q${q.id} · ${escapeHtml(q.category)}</span>
      </div>
      <strong style="font-size:0.88rem;">"${escapeHtml(q.question)}"</strong>
      <div class="muted">💡 <em>Why interviewers ask this:</em> ${escapeHtml(q.why_asked)}</div>
      <div class="star-grid">
        <div class="star-cell"><strong>S — Situation:</strong> ${escapeHtml(sg.Situation || "")}</div>
        <div class="star-cell"><strong>T — Task:</strong> ${escapeHtml(sg.Task || "")}</div>
        <div class="star-cell"><strong>A — Action:</strong> ${escapeHtml(sg.Action || "")}</div>
        <div class="star-cell"><strong>R — Result:</strong> ${escapeHtml(sg.Result || "")}</div>
      </div>
    `;
    els.interviewList.appendChild(card);
  });
}

function renderStatsAndHistory(stats, recent) {
  if (stats) {
    els.statScans.textContent = `${stats.total_scans || 0} scans`;
    els.statBest.textContent = `Best: ${stats.best_score ? stats.best_score + "%" : "—"}`;
    els.statAvg.textContent = `Avg: ${stats.avg_score ? stats.avg_score + "%" : "—"}`;
  }
  els.historyList.innerHTML = "";
  if (!recent || !recent.length) {
    els.historyList.innerHTML = `<li class="history-empty">No scans saved yet.</li>`;
    return;
  }
  recent.forEach((item) => {
    const li = document.createElement("li");
    li.className = "history-item";
    const badgeClass =
      item.tier === "high" ? "badge--success" : item.tier === "low" ? "badge--warn" : "badge--accent";
    li.innerHTML = `
      <span><strong>${escapeHtml(item.role_title)}</strong> <small class="muted">(${escapeHtml(item.company_name || "Target")})</small></span>
      <span class="badge ${badgeClass}">${item.overall_score}%</span>
    `;
    els.historyList.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// UI Utilities
// ---------------------------------------------------------------------------

function setSubbar(valEl, barEl, pct) {
  const clamped = Math.max(0, Math.min(100, Number(pct) || 0));
  valEl.textContent = `${clamped}%`;
  barEl.style.width = `${clamped}%`;
}

function switchTab(tabName) {
  els.tabBtns.forEach((btn) => {
    const active = btn.dataset.tab === tabName;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-selected", String(active));
  });
  ["radar", "bullets", "cover", "interview"].forEach((name) => {
    const pane = $(`#tab-${name}`);
    if (pane) {
      pane.hidden = name !== tabName;
      pane.classList.toggle("is-active", name === tabName);
    }
  });
}

function setConnectionStatus(online, text) {
  els.connDot.classList.toggle("is-online", online);
  els.connLabel.textContent = text;
}

function setButtonsDisabled(disabled) {
  [els.scanBtn, els.quickRewriteBtn, els.runBulletsBtn, els.runCoverBtn, els.runInterviewBtn].forEach(
    (b) => {
      if (b) b.disabled = disabled;
    }
  );
}

let statusTimeout = null;
function showStatus(msg, kind = "info") {
  els.statusBanner.hidden = false;
  els.statusBanner.dataset.kind = kind;
  els.statusText.textContent = msg;
  clearTimeout(statusTimeout);
  statusTimeout = setTimeout(() => {
    els.statusBanner.hidden = true;
  }, 4500);
}

async function copyText(text, toastMsg) {
  try {
    await navigator.clipboard.writeText(text);
    showStatus(toastMsg, "success");
  } catch {
    showStatus("Copied!", "success");
  }
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(str) {
  return escapeHtml(str).replace(/'/g, "&#39;");
}

init();
