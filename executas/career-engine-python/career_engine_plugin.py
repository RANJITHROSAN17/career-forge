#!/usr/bin/env python3
"""
career-engine — Executa stdio tool plugin for Career Forge (AI Resume & Job Match Studio)

Persists scan history and active analysis state to ``~/.anna/career-forge/state.json``
and exposes ONE dispatcher tool method (``career``) with an ``action`` discriminator:
    - analyze
    - rewrite_bullets
    - cover_letter
    - interview_prep
    - get_state
    - clear_history

Protocol: JSON-RPC 2.0 over stdio
Methods:  describe, invoke, health
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Plugin manifest — Anna calls ``describe`` and uses this dict verbatim.
# ---------------------------------------------------------------------------
MANIFEST: dict[str, Any] = {
    "display_name": "Career Engine",
    "version": "1.0.1",
    "description": (
        "ATS resume & job match analysis engine, XYZ bullet rewriter, tailored "
        "cover letter generator, and STAR interview prep studio. Persists state "
        "to ~/.anna/career-forge/state.json."
    ),
    "author": "Career Forge Builder",
    "homepage": "https://anna.partners",
    "license": "MIT",
    "tags": ["career", "resume", "ats", "job-match", "interview-prep", "anna-app"],
    "tools": [
        {
            "name": "career",
            "description": (
                "Run ATS resume & job match analysis or generate career artifacts. "
                "Use `action` to select: analyze | rewrite_bullets | cover_letter | "
                "interview_prep | get_state | clear_history."
            ),
            "parameters": [
                {
                    "name": "action",
                    "type": "string",
                    "description": (
                        "Operation to run: analyze | rewrite_bullets | cover_letter | "
                        "interview_prep | get_state | clear_history."
                    ),
                    "required": True,
                },
                {
                    "name": "resume_text",
                    "type": "string",
                    "description": "Candidate resume text (required for analyze; optional for others if a scan is active).",
                    "required": False,
                    "default": "",
                },
                {
                    "name": "job_description",
                    "type": "string",
                    "description": "Target job description text (required for analyze; optional for others if a scan is active).",
                    "required": False,
                    "default": "",
                },
                {
                    "name": "role_title",
                    "type": "string",
                    "description": "Target role title (e.g., 'Senior Full-Stack AI Engineer').",
                    "required": False,
                    "default": "",
                },
                {
                    "name": "company_name",
                    "type": "string",
                    "description": "Target company name (optional, used in cover_letter and interview_prep).",
                    "required": False,
                    "default": "",
                },
                {
                    "name": "tone",
                    "type": "string",
                    "description": "Tone for cover_letter: modern | technical | executive.",
                    "required": False,
                    "default": "modern",
                },
            ],
        },
    ],
    "runtime": {"type": "uv", "min_version": "0.1.0"},
}

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
STATE_DIR = Path(os.path.expanduser("~/.anna/career-forge"))
STATE_FILE = STATE_DIR / "state.json"
MAX_HISTORY = 50


def _now() -> float:
    return time.time()


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"active_scan": None, "history": []}
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("state.json root must be an object")
        data.setdefault("active_scan", None)
        data.setdefault("history", [])
        return data
    except (json.JSONDecodeError, ValueError, OSError):
        return {"active_scan": None, "history": []}


def _save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp.replace(STATE_FILE)


def _compute_stats(history: list[dict[str, Any]]) -> dict[str, Any]:
    if not history:
        return {
            "total_scans": 0,
            "best_score": 0,
            "avg_score": 0,
            "roles_analyzed": 0,
        }
    scores = [int(h.get("overall_score", 0)) for h in history]
    roles = {h.get("role_title", "").strip().lower() for h in history if h.get("role_title")}
    return {
        "total_scans": len(history),
        "best_score": max(scores) if scores else 0,
        "avg_score": round(sum(scores) / len(scores)) if scores else 0,
        "roles_analyzed": max(1, len(roles)),
    }


# ---------------------------------------------------------------------------
# Curated Skill & Keyword Taxonomy for Deterministic ATS Analysis
# ---------------------------------------------------------------------------
SKILL_TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Languages & Core": {
        "Python": ["python", "py", "python3"],
        "TypeScript": ["typescript", "ts"],
        "JavaScript": ["javascript", "js", "es6", "ecmascript"],
        "Go": ["golang", "go "],
        "Rust": ["rust"],
        "Java": ["java"],
        "C++": ["c++", "cpp"],
        "SQL": ["sql", "postgres", "postgresql", "mysql", "sqlite", "snowflake", "bigquery"],
        "GraphQL": ["graphql", "gql"],
        "HTML/CSS": ["html", "css", "tailwind", "scss"],
    },
    "AI, ML & Data": {
        "LLM Agents": ["llm", "large language model", "ai agent", "agents", "agentic", "multi-agent"],
        "RAG & Vector DB": ["rag", "retrieval-augmented", "vector database", "pinecone", "pgvector", "qdrant", "weaviate", "milvus", "faiss"],
        "LangChain / LlamaIndex": ["langchain", "langgraph", "llamaindex"],
        "Prompt Engineering": ["prompt engineering", "few-shot", "chain-of-thought", "evals", "llm evaluation"],
        "PyTorch / TensorFlow": ["pytorch", "tensorflow", "keras", "jax", "scikit-learn", "sklearn"],
        "Fine-Tuning & RLHF": ["fine-tuning", "lora", "qlora", "rlhf", "peft", "huggingface", "transformers"],
        "MCP / Tool Calling": ["mcp", "model context protocol", "tool calling", "function calling", "json-rpc"],
        "Data Pipelines": ["spark", "airflow", "kafka", "dbt", "etl", "data pipeline", "pandas", "polars"],
        "A/B Testing & Experimentation": ["a/b test", "experimentation", "causal inference", "statistical", "hypothesis"],
    },
    "Frameworks & Backend": {
        "React / Next.js": ["react", "next.js", "nextjs", "redux", "vite"],
        "Node.js / Express": ["node.js", "nodejs", "express", "nestjs", "fastify"],
        "FastAPI / Flask / Django": ["fastapi", "flask", "django", "pydantic", "asyncio"],
        "Microservices & APIs": ["microservices", "rest api", "restful", "grpc", "websocket", "sse"],
        "Distributed Systems": ["distributed systems", "high availability", "scalability", "concurrency", "caching", "redis"],
    },
    "Cloud, DevOps & MLOps": {
        "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "sagemaker", "bedrock"],
        "GCP / Azure": ["gcp", "google cloud", "azure", "vertex ai"],
        "Docker & Kubernetes": ["docker", "kubernetes", "k8s", "helm", "container"],
        "CI/CD & Automation": ["ci/cd", "github actions", "gitlab ci", "jenkins", "terraform", "iac"],
        "Observability & Monitoring": ["prometheus", "grafana", "datadog", "opentelemetry", "sentry", "logging", "telemetry"],
        "Security & Auth": ["oauth", "jwt", "rbac", "soc2", "security", "encryption"],
    },
    "Product & Leadership": {
        "Product Strategy & Roadmap": ["roadmap", "product strategy", "prd", "go-to-market", "gtm", "product lifecycle"],
        "Agile & Cross-Functional": ["agile", "scrum", "sprint", "cross-functional", "stakeholder"],
        "User Research & Analytics": ["user research", "funnel", "retention", "mau", "kpi", "okr", "cohort", "mixpanel", "amplitude"],
        "Technical Mentorship": ["mentored", "led a team", "code review", "tech lead", "architecture review", "hiring"],
    },
}

STRONG_VERBS = {
    "architected", "engineered", "built", "designed", "spearheaded", "launched",
    "optimized", "reduced", "increased", "accelerated", "automated", "scaled",
    "delivered", "implemented", "pioneered", "transformed", "orchestrated",
    "led", "mentored", "streamlined", "deployed", "developed", "refactored",
    "achieved", "generated", "negotiated", "resolved", "integrated",
}

WEAK_PHRASES = [
    "responsible for",
    "worked on",
    "helped with",
    "assisted in",
    "duties included",
    "was involved in",
    "participated in",
    "tasked with",
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "will", "have",
    "are", "you", "our", "work", "working", "team", "role", "experience", "years",
    "using", "such", "into", "about", "who", "what", "when", "where", "why", "how",
    "able", "must", "should", "plus", "preferred", "strong", "good", "great",
    "building", "build", "join", "looking", "seeking", "including", "across",
    "within", "through", "both", "other", "more", "most", "some", "any", "all",
    "senior", "junior", "staff", "principal", "lead", "engineer", "engineering",
    "developer", "manager", "director", "architect", "specialist", "analyst",
    "scientist", "hiring", "company", "product", "platform", "systems", "system",
    "services", "service", "solutions", "applications", "application", "vector",
    "pipelines", "pipeline", "models", "model", "data", "cloud", "software",
    "full-stack", "fullstack", "backend", "frontend", "design", "production",
}


def _normalize(text: str) -> str:
    return " " + re.sub(r"\s+", " ", (text or "").lower()) + " "


def _detect_skills(text: str) -> dict[str, dict[str, Any]]:
    norm = _normalize(text)
    found: dict[str, dict[str, Any]] = {}
    for category, skills in SKILL_TAXONOMY.items():
        for canonical, aliases in skills.items():
            count = 0
            for alias in aliases:
                pattern = r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])"
                matches = re.findall(pattern, norm)
                count += len(matches)
            if count > 0:
                found[canonical] = {"category": category, "count": count}
    return found


def _extract_custom_jd_terms(jd_text: str, existing_canonical: set[str]) -> list[str]:
    """Find capitalized technical tokens or domain terms in JD not already in taxonomy."""
    already_lower = {c.lower() for c in existing_canonical}
    for cat in SKILL_TAXONOMY.values():
        for aliases in cat.values():
            for a in aliases:
                already_lower.add(a.strip().lower())

    tokens = re.findall(r"\b[A-Z][A-Za-z0-9+#.\-]{2,18}\b", jd_text or "")
    freq: dict[str, int] = {}
    for tok in tokens:
        low = tok.lower()
        if low in STOPWORDS or low in already_lower or len(low) < 3:
            continue
        freq[tok] = freq.get(tok, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in ranked[:6]]


def _extract_bullets(resume_text: str) -> list[str]:
    lines = [ln.strip() for ln in (resume_text or "").splitlines() if ln.strip()]
    bullets: list[str] = []
    for ln in lines:
        cleaned = re.sub(r"^[\-\*•‣▪▸\d+.\)]+\s*", "", ln).strip()
        if len(cleaned.split()) >= 6 and len(cleaned) >= 35:
            # Skip obvious header lines or contact lines
            if "@" in cleaned or "linkedin.com" in cleaned.lower() or "github.com" in cleaned.lower():
                continue
            bullets.append(cleaned)
    return bullets[:12]


def _has_quantified_metric(bullet: str) -> bool:
    patterns = [
        r"\b\d+(?:\.\d+)?%",               # percentages: 42%, 99.9%
        r"\$\d+(?:[.,]\d+)?[kKmMbB]?",     # currency: $50K, $1.2M
        r"\b\d+(?:\.\d+)?x\b",             # multipliers: 3x, 10x
        r"\b\d+\+?\s*(?:users|customers|clients|engineers|developers|requests|ms|seconds|mins|hours|days|months|pipelines|models|endpoints|services|microservices|repos|stars|downloads|mau|dau)\b",
    ]
    low = bullet.lower()
    return any(re.search(p, low) for p in patterns)


def _audit_bullets(bullets: list[str], missing_skills: list[str]) -> list[dict[str, Any]]:
    audited: list[dict[str, Any]] = []
    for idx, b in enumerate(bullets):
        words = re.findall(r"[a-zA-Z]+", b)
        first_word = words[0].lower() if words else ""
        has_metric = _has_quantified_metric(b)
        strong_start = first_word in STRONG_VERBS
        weak_match = next((w for w in WEAK_PHRASES if w in b.lower()), None)

        issues: list[str] = []
        if not has_metric:
            issues.append("Missing measurable metric (%, $, latency, scale, or time saved)")
        if weak_match:
            issues.append(f"Contains passive phrasing ('{weak_match}')")
        elif not strong_start:
            issues.append("Could open with a stronger executive action verb")

        status = "strong" if (has_metric and strong_start and not weak_match) else ("needs_metric" if not has_metric else "polish")
        inject_skill = missing_skills[idx % len(missing_skills)] if missing_skills else "production observability"
        upgraded = _synthesize_xyz_bullet(b, inject_skill)

        audited.append({
            "index": idx + 1,
            "original": b,
            "has_metric": has_metric,
            "strong_verb": strong_start,
            "status": status,
            "issues": issues,
            "suggested_keyword": inject_skill,
            "xyz_rewrite": upgraded["impact_variant"],
            "keyword_rewrite": upgraded["keyword_variant"],
        })
    return audited


def _synthesize_xyz_bullet(original: str, target_keyword: str) -> dict[str, str]:
    clean = original.rstrip(".")
    # Strip weak openers
    for wp in WEAK_PHRASES:
        clean = re.sub(r"^" + re.escape(wp) + r"\s+", "", clean, flags=re.IGNORECASE)
    words = clean.split()
    if not words:
        return {
            "impact_variant": f"Architected scalable {target_keyword} workflows, reducing end-to-end processing latency by 38% across production workloads.",
            "keyword_variant": f"Engineered production-grade {target_keyword} integration with automated validation, achieving 99.9% reliability.",
        }
    first_lower = re.sub(r"[^a-z]", "", words[0].lower())
    if first_lower not in STRONG_VERBS:
        core_phrase = clean[0].lower() + clean[1:] if len(clean) > 1 else clean.lower()
        verb = "Engineered and scaled"
    else:
        verb = words[0].capitalize()
        core_phrase = " ".join(words[1:])

    has_metric = _has_quantified_metric(original)
    metric_tail = (
        f", leveraging {target_keyword} to improve throughput and reliability across production runs."
        if has_metric
        else f", cutting p95 turnaround time by 35% and boosting workflow reliability across 10K+ monthly runs using {target_keyword}."
    )
    impact_variant = f"{verb} {core_phrase}{metric_tail}"
    keyword_variant = (
        f"Spearheaded {target_keyword}-driven architecture to {core_phrase.lstrip('to ')}, "
        f"delivering measurable 40% efficiency gains and automated quality gates."
    )
    return {
        "impact_variant": impact_variant,
        "keyword_variant": keyword_variant,
    }


# ---------------------------------------------------------------------------
# Core Actions
# ---------------------------------------------------------------------------

def _action_analyze(
    resume_text: str,
    job_description: str,
    role_title: str = "",
    company_name: str = "",
) -> dict[str, Any]:
    resume_text = (resume_text or "").strip()
    job_description = (job_description or "").strip()
    if not resume_text:
        raise ValueError("resume_text is required for action='analyze'")
    if not job_description:
        raise ValueError("job_description is required for action='analyze'")

    role_title = (role_title or "").strip() or "Target AI / Software Engineering Role"
    company_name = (company_name or "").strip() or "Target Organization"

    resume_skills = _detect_skills(resume_text)
    jd_skills = _detect_skills(job_description)

    matched_keywords: list[dict[str, Any]] = []
    missing_keywords: list[dict[str, Any]] = []

    for skill_name, jd_meta in jd_skills.items():
        if skill_name in resume_skills:
            matched_keywords.append({
                "skill": skill_name,
                "category": jd_meta["category"],
                "resume_mentions": resume_skills[skill_name]["count"],
                "jd_mentions": jd_meta["count"],
            })
        else:
            priority = "High Priority" if jd_meta["count"] >= 2 or jd_meta["category"] in ("AI, ML & Data", "Languages & Core") else "Recommended"
            missing_keywords.append({
                "skill": skill_name,
                "category": jd_meta["category"],
                "jd_mentions": jd_meta["count"],
                "priority": priority,
                "placement_tip": f"Add '{skill_name}' to your Technical Skills section and weave it into 1 quantified experience bullet.",
            })

    # Also check custom capitalized terms in JD if taxonomy had few hits
    custom_terms = _extract_custom_jd_terms(job_description, set(jd_skills.keys()) | set(resume_skills.keys()))
    norm_res = _normalize(resume_text)
    for term in custom_terms[:4]:
        if term.lower() in norm_res:
            matched_keywords.append({
                "skill": term,
                "category": "Domain & Role Terms",
                "resume_mentions": 1,
                "jd_mentions": 1,
            })
        else:
            missing_keywords.append({
                "skill": term,
                "category": "Domain & Role Terms",
                "jd_mentions": 1,
                "priority": "Recommended",
                "placement_tip": f"Mirror the exact term '{term}' from the job description in your summary or project bullets.",
            })

    # Sort matched and missing
    matched_keywords.sort(key=lambda x: (-x["jd_mentions"], x["skill"]))
    missing_keywords.sort(key=lambda x: (0 if x["priority"] == "High Priority" else 1, -x["jd_mentions"], x["skill"]))

    # Additional bonus skills on resume not explicitly in JD
    bonus_skills = [
        {"skill": s, "category": m["category"]}
        for s, m in resume_skills.items()
        if s not in jd_skills
    ][:8]

    bullets = _extract_bullets(resume_text)
    missing_skill_names = [m["skill"] for m in missing_keywords]
    audited_bullets = _audit_bullets(bullets, missing_skill_names)

    # Compute 4 sub-scores
    total_jd_targets = len(matched_keywords) + len(missing_keywords)
    if total_jd_targets > 0:
        raw_ratio = len(matched_keywords) / total_jd_targets
        technical_match = min(98, max(32, round(raw_ratio * 100)))
    else:
        technical_match = 72

    # Keyword alignment considers multi-mention coverage
    keyword_alignment = min(98, max(35, round(technical_match * 0.92 + min(12, len(matched_keywords) * 2))))

    # Quantified impact score
    if audited_bullets:
        quant_count = sum(1 for b in audited_bullets if b["has_metric"])
        strong_verb_count = sum(1 for b in audited_bullets if b["strong_verb"])
        quantified_impact = min(98, max(28, round((quant_count / len(audited_bullets)) * 75 + (strong_verb_count / len(audited_bullets)) * 25)))
    else:
        quantified_impact = 45

    # ATS Readiness checks
    has_email = bool(re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", resume_text))
    has_link = bool(re.search(r"(?:github\.com|linkedin\.com|https?://)", resume_text.lower()))
    word_count = len(resume_text.split())
    good_length = 120 <= word_count <= 950
    has_sections = sum(
        1 for sec in ("experience", "skills", "education", "projects", "summary")
        if sec in resume_text.lower()
    ) >= 2

    readiness_points = (
        (25 if has_email else 10)
        + (20 if has_link else 8)
        + (25 if good_length else 14)
        + (30 if has_sections else 15)
    )
    ats_readiness = min(99, max(40, readiness_points))

    overall_score = round(
        technical_match * 0.38
        + keyword_alignment * 0.24
        + quantified_impact * 0.23
        + ats_readiness * 0.15
    )

    if overall_score >= 82:
        verdict = "Strong ATS Match — Ready for Fast-Track Shortlist"
        tier = "high"
    elif overall_score >= 65:
        verdict = "Competitive Foundation — Add Missing Keywords & Metrics to Hit 85+"
        tier = "medium"
    else:
        verdict = "High Gap Detected — Tailor Skills & Quantify Bullets Before Submitting"
        tier = "low"

    section_checks = [
        {
            "label": "Contact & Portfolio Links",
            "passed": has_email and has_link,
            "detail": "Email + GitHub/LinkedIn detected" if (has_email and has_link) else "Add direct email and GitHub/LinkedIn URL in header",
        },
        {
            "label": "Core JD Skill Coverage",
            "passed": technical_match >= 70,
            "detail": f"Matched {len(matched_keywords)} of {total_jd_targets} target job skills ({technical_match}%)",
        },
        {
            "label": "Quantified Impact Density",
            "passed": quantified_impact >= 70,
            "detail": f"{sum(1 for b in audited_bullets if b['has_metric'])}/{len(audited_bullets) or 1} experience bullets include hard metrics (%, $, latency, scale)",
        },
        {
            "label": "ATS Standard Section Structure",
            "passed": has_sections and good_length,
            "detail": f"{word_count} words analyzed across standard ATS-parseable headings",
        },
    ]

    top_priorities: list[str] = []
    if missing_keywords:
        top3_missing = ", ".join(m["skill"] for m in missing_keywords[:3])
        top_priorities.append(
            f"Integrate high-priority missing keywords ({top3_missing}) into your Skills block and top 2 experience bullets."
        )
    unquantified = [b for b in audited_bullets if not b["has_metric"]]
    if unquantified:
        top_priorities.append(
            f"Quantify {len(unquantified)} experience bullet(s) using the XYZ formula (add % improvement, latency reduction, or user scale)."
        )
    if not (has_email and has_link):
        top_priorities.append(
            "Include a clickable GitHub/portfolio link and professional email at the top of your resume."
        )
    if len(top_priorities) < 3:
        top_priorities.append(
            f"Mirror the exact role title '{role_title}' in your Resume Headline / Summary to maximize ATS title-weight scoring."
        )

    scan_record: dict[str, Any] = {
        "scan_id": uuid.uuid4().hex[:10],
        "timestamp": _now(),
        "role_title": role_title,
        "company_name": company_name,
        "overall_score": overall_score,
        "verdict": verdict,
        "tier": tier,
        "sub_scores": {
            "technical_match": technical_match,
            "keyword_alignment": keyword_alignment,
            "quantified_impact": quantified_impact,
            "ats_readiness": ats_readiness,
        },
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "bonus_skills": bonus_skills,
        "bullet_audits": audited_bullets,
        "section_checks": section_checks,
        "top_priorities": top_priorities[:3],
        "resume_text": resume_text,
        "job_description": job_description,
    }

    state = _load_state()
    state["active_scan"] = scan_record
    history_summary = {
        "scan_id": scan_record["scan_id"],
        "timestamp": scan_record["timestamp"],
        "role_title": role_title,
        "company_name": company_name,
        "overall_score": overall_score,
        "tier": tier,
        "matched_count": len(matched_keywords),
        "missing_count": len(missing_keywords),
    }
    history = state.get("history", [])
    history.insert(0, history_summary)
    state["history"] = history[:MAX_HISTORY]
    _save_state(state)

    return {
        "scan": scan_record,
        "stats": _compute_stats(state["history"]),
        "recent": state["history"][:10],
    }


def _action_rewrite_bullets(
    resume_text: str = "",
    job_description: str = "",
) -> dict[str, Any]:
    state = _load_state()
    active = state.get("active_scan") or {}
    res = (resume_text or active.get("resume_text") or "").strip()
    jd = (job_description or active.get("job_description") or "").strip()
    if not res:
        raise ValueError("Please run an ATS scan first or provide resume_text.")

    jd_skills = _detect_skills(jd) if jd else {}
    res_skills = _detect_skills(res)
    missing = [s for s in jd_skills if s not in res_skills]
    if not missing:
        missing = list(jd_skills.keys()) or ["LLM Agents", "FastAPI", "CI/CD"]

    bullets = _extract_bullets(res)
    if not bullets:
        bullets = [res[:180]]

    rewrites = _audit_bullets(bullets, missing)
    combined_markdown = "\n".join(f"• {r['xyz_rewrite']}" for r in rewrites)

    return {
        "role_title": active.get("role_title", "Target Role"),
        "injected_keywords": missing[:6],
        "rewrites": rewrites,
        "copy_ready_block": combined_markdown,
    }


def _action_cover_letter(
    resume_text: str = "",
    job_description: str = "",
    role_title: str = "",
    company_name: str = "",
    tone: str = "modern",
) -> dict[str, Any]:
    state = _load_state()
    active = state.get("active_scan") or {}
    res = (resume_text or active.get("resume_text") or "").strip()
    jd = (job_description or active.get("job_description") or "").strip()
    role = (role_title or active.get("role_title") or "Senior Engineer").strip()
    company = (company_name or active.get("company_name") or "your engineering organization").strip()
    tone = (tone or "modern").strip().lower()

    if not res:
        raise ValueError("Please run an ATS scan first or provide resume_text.")

    res_skills = list(_detect_skills(res).keys())
    jd_skills = list(_detect_skills(jd).keys()) if jd else []
    shared = [s for s in jd_skills if s in res_skills] or res_skills[:4] or ["Python", "AI Systems", "Scalable APIs"]
    top_skills_str = ", ".join(shared[:4])

    bullets = _extract_bullets(res)
    highlight_1 = bullets[0] if bullets else "building production AI applications with measurable latency and reliability gains"
    highlight_2 = bullets[1] if len(bullets) > 1 else "collaborating across product and engineering to ship user-facing features fast"

    if tone == "executive":
        opening = (
            f"Dear Hiring Team at {company},\n\n"
            f"With a proven track record of architecting high-leverage technical systems and translating complex requirements into measurable business outcomes, I am writing to express my strong interest in the {role} position."
        )
    elif tone == "technical":
        opening = (
            f"Hi {company} Engineering Team,\n\n"
            f"I'm reaching out for the {role} role because my hands-on stack across {top_skills_str} directly aligns with the technical architecture and reliability challenges outlined in your job specification."
        )
    else:
        opening = (
            f"Hi {company} Team,\n\n"
            f"I'm excited to apply for the {role} position. Having built and scaled production systems using {top_skills_str}, I love turning ambitious product ideas into fast, reliable user experiences."
        )

    cover_letter_text = (
        f"{opening}\n\n"
        f"Across my recent work, I've focused on measurable engineering impact:\n"
        f"• {highlight_1}\n"
        f"• {highlight_2}\n\n"
        f"What excites me most about {company} is the emphasis on shipping high-impact systems where { ', '.join(shared[:2]) if len(shared) >= 2 else top_skills_str } directly drive user value. I bring both deep execution speed and a strong habit of instrumenting metrics from day one.\n\n"
        f"I'd welcome a 15-minute conversation to walk through how my background in {top_skills_str} can help accelerate your upcoming roadmap.\n\n"
        f"Best regards,\n[Your Name]"
    )

    linkedin_dm = (
        f"Hi! I just applied for the {role} role at {company}. My recent work with {top_skills_str} "
        f"closely mirrors your stack—would love to share a quick demo or connect for 10 mins if helpful!"
    )

    email_subject = f"Application: {role} — Proven { ', '.join(shared[:3]) } Builder"

    return {
        "role_title": role,
        "company_name": company,
        "tone": tone,
        "highlighted_skills": shared[:5],
        "email_subject": email_subject,
        "cover_letter": cover_letter_text,
        "linkedin_dm": linkedin_dm,
    }


def _action_interview_prep(
    resume_text: str = "",
    job_description: str = "",
    role_title: str = "",
) -> dict[str, Any]:
    state = _load_state()
    active = state.get("active_scan") or {}
    res = (resume_text or active.get("resume_text") or "").strip()
    jd = (job_description or active.get("job_description") or "").strip()
    role = (role_title or active.get("role_title") or "Target Engineering Role").strip()

    if not res:
        raise ValueError("Please run an ATS scan first or provide resume_text.")

    matched = [m["skill"] for m in active.get("matched_keywords", [])] or list(_detect_skills(res).keys())
    missing = [m["skill"] for m in active.get("missing_keywords", [])]

    core_skill_1 = matched[0] if matched else "Python & API Architecture"
    core_skill_2 = matched[1] if len(matched) > 1 else "Distributed Systems"
    gap_skill = missing[0] if missing else "Production Observability & Scaling"

    questions = [
        {
            "id": 1,
            "category": "Technical Depth",
            "question": f"Walk me through the most complex production system you built using {core_skill_1}. What were the hardest trade-offs?",
            "why_asked": f"Verifies hands-on depth in {core_skill_1} (a primary matched keyword on your resume).",
            "star_guide": {
                "Situation": f"Describe the production scale, latency, or reliability bottleneck you faced with {core_skill_1}.",
                "Task": "Define the concrete SLA or target metric you were responsible for hitting.",
                "Action": f"Explain why you chose {core_skill_1}, how you structured the architecture, and how you tested edge cases.",
                "Result": "Share the exact before/after metric (e.g., p95 latency drop, throughput gain, or hours saved).",
            },
        },
        {
            "id": 2,
            "category": "System Design & Scale",
            "question": f"If traffic or workload volume increased 10x tomorrow for a service combining {core_skill_1} and {core_skill_2}, what breaks first and how would you redesign it?",
            "why_asked": f"Tests architectural maturity for {role} beyond writing single-node code.",
            "star_guide": {
                "Situation": "Identify the primary stateful bottleneck (DB connections, LLM rate limits, queue backpressure).",
                "Task": "Maintain high availability and predictable cost under 10x load.",
                "Action": "Propose caching, async workers/queues, horizontal autoscaling, and circuit breakers.",
                "Result": "Quantify how the architecture degrades gracefully without dropping user requests.",
            },
        },
        {
            "id": 3,
            "category": "Skill Gap Mitigation",
            "question": f"Our team relies heavily on {gap_skill}. How have you approached similar problems, and how would you ramp up in your first 30 days?",
            "why_asked": f"Directly addresses '{gap_skill}', which appeared in the Job Description but was missing or light on your resume.",
            "star_guide": {
                "Situation": f"Acknowledge your adjacent experience with {core_skill_1} and how the underlying concepts map to {gap_skill}.",
                "Task": "Show low-risk, fast onboarding into the team's production workflow.",
                "Action": f"Detail a concrete prototype or side benchmark you built (or are building) with {gap_skill}.",
                "Result": "Reassure the interviewer with a prior example where you mastered a new stack in under 2 weeks.",
            },
        },
        {
            "id": 4,
            "category": "Behavioral (STAR)",
            "question": "Tell me about a time when a project requirement changed late in the cycle or a production deployment failed. How did you handle it?",
            "why_asked": "Evaluates ownership, incident communication, and bias for action under pressure.",
            "star_guide": {
                "Situation": "Pick a real high-stakes release or shifting product spec.",
                "Task": "Protect user trust and keep the critical path unblocked.",
                "Action": "Explain how you triaged root cause, aligned stakeholders, and shipped a scoped mitigation.",
                "Result": "Highlight the post-mortem improvement (automated tests, canary checks) that prevented recurrence.",
            },
        },
        {
            "id": 5,
            "category": "Role Alignment & 90-Day Impact",
            "question": f"Why are you targeting this {role} position right now, and what would a successful first 60 days look like for you?",
            "why_asked": "Tests genuine motivation and whether you think in terms of shipping user/business outcomes.",
            "star_guide": {
                "Situation": "Connect your strongest career wins directly to the team's core mission.",
                "Task": "Deliver early, visible wins while learning the codebase and domain.",
                "Action": "Week 1-2: ship a high-signal fix & map architecture; Day 30-60: own a full feature end-to-end.",
                "Result": "Leave the interviewer picturing you already operating as a trusted teammate.",
            },
        },
    ]

    return {
        "role_title": role,
        "focus_skills": [core_skill_1, core_skill_2],
        "gap_focus": gap_skill,
        "questions": questions,
    }


def _action_get_state() -> dict[str, Any]:
    state = _load_state()
    history = state.get("history", [])
    return {
        "active_scan": state.get("active_scan"),
        "stats": _compute_stats(history),
        "recent": history[:10],
    }


def _action_clear_history() -> dict[str, Any]:
    state = {"active_scan": None, "history": []}
    _save_state(state)
    return {
        "active_scan": None,
        "stats": _compute_stats([]),
        "recent": [],
        "message": "Scan history cleared.",
    }


def tool_career(
    action: str,
    resume_text: str = "",
    job_description: str = "",
    role_title: str = "",
    company_name: str = "",
    tone: str = "modern",
) -> dict[str, Any]:
    if action == "analyze":
        return _action_analyze(resume_text, job_description, role_title, company_name)
    if action == "rewrite_bullets":
        return _action_rewrite_bullets(resume_text, job_description)
    if action == "cover_letter":
        return _action_cover_letter(resume_text, job_description, role_title, company_name, tone)
    if action == "interview_prep":
        return _action_interview_prep(resume_text, job_description, role_title)
    if action == "get_state":
        return _action_get_state()
    if action == "clear_history":
        return _action_clear_history()
    raise ValueError(
        f"unknown action: {action!r}; expected one of "
        "analyze | rewrite_bullets | cover_letter | interview_prep | get_state | clear_history"
    )


TOOL_DISPATCH = {"career": tool_career}


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 Handlers (stdio protocol required by Anna Executa)
# ---------------------------------------------------------------------------

def handle_describe(_params: dict[str, Any]) -> dict[str, Any]:
    return MANIFEST


def handle_invoke(params: dict[str, Any]) -> dict[str, Any]:
    tool_name = params.get("tool")
    args = params.get("arguments") or {}
    if not isinstance(args, dict):
        raise ValueError("`arguments` must be an object")
    fn = TOOL_DISPATCH.get(tool_name)
    if fn is None:
        raise ValueError(f"unknown tool: {tool_name!r}")
    try:
        payload = fn(**args)
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"success": True, "data": payload}


def handle_health(_params: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ready", "state_file": str(STATE_FILE)}


METHOD_DISPATCH = {
    "describe": handle_describe,
    "invoke": handle_invoke,
    "health": handle_health,
}


def send(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    print(
        f"[career-engine] {MANIFEST['display_name']} v{MANIFEST['version']} ready",
        file=sys.stderr,
    )
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"parse error: {e}"},
                }
            )
            continue

        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}
        handler = METHOD_DISPATCH.get(method)
        if handler is None:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"method not found: {method}"},
                }
            )
            continue
        try:
            result = handler(params)
            send({"jsonrpc": "2.0", "id": req_id, "result": result})
        except Exception as exc:  # noqa: BLE001
            send(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(exc)},
                }
            )


if __name__ == "__main__":
    main()
