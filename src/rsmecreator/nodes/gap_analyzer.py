"""
Gap Analyzer Node

Compares resume vs JD to identify:
- Matched skills
- Missing keywords
- Strengths and gaps
"""

import json
from datetime import datetime
from ..state import ResumeState
from ..config import get_llm
from ..logging_config import get_logger

logger = get_logger("nodes.gap_analyzer")


def _normalize_for_match(text: str) -> set:
    """Normalize text for keyword matching."""
    return set(w.lower().strip() for w in text.replace(",", " ").split() if len(w) > 2)


def gap_analyzer_node(state: ResumeState) -> ResumeState:
    """Analyze gaps between resume and JD."""
    parsed_resume = state.get("parsed_resume", {})
    jd_keywords = state.get("jd_keywords", [])
    jd_requirements = state.get("jd_requirements", [])

    # Build resume text for matching
    resume_text = json.dumps(parsed_resume) if isinstance(parsed_resume, dict) else str(parsed_resume)
    resume_words = _normalize_for_match(resume_text)

    # Simple keyword matching
    jd_keywords_flat = [k for k in jd_keywords if isinstance(k, str)]
    matched = []
    missing = []
    for kw in jd_keywords_flat:
        kw_norm = kw.lower()
        if kw_norm in resume_words or any(kw_norm in w or w in kw_norm for w in resume_words):
            matched.append(kw)
        else:
            missing.append(kw)

    # Use LLM for richer gap analysis
    llm = get_llm()
    prompt = f"""As a resume expert, analyze the gap between this resume and job description.

RESUME (parsed):
{json.dumps(parsed_resume, indent=2)[:4000]}

JOB REQUIREMENTS: {jd_requirements[:15]}
JOB KEYWORDS: {jd_keywords[:20]}

Return JSON with:
- strengths: list of resume strengths that match the JD
- gaps: list of JD requirements/keywords not well addressed in resume
- suggestions: list of 3-5 concrete suggestions to tailor the resume (rewrite bullets, add keywords, reorder)
- emphasize: list of existing resume items to emphasize or expand

Return ONLY valid JSON. No markdown.
JSON:"""
    try:
        resp = llm.invoke(prompt)
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        gap_analysis = json.loads(content)
    except Exception as e:
        logger.warning("LLM gap analysis failed, using fallback: %s", e)
        gap_analysis = {
            "strengths": ["Resume contains relevant experience"],
            "gaps": missing[:5],
            "suggestions": [f"Add or emphasize: {m}" for m in missing[:3]],
            "emphasize": [],
        }

    gap_analysis["matched_keywords"] = matched
    gap_analysis["missing_keywords"] = missing

    logger.info("Gap analyzed | matched=%d | missing=%d", len(matched), len(missing))
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "gap_analyzer",
        "matched_count": len(matched),
        "missing_count": len(missing),
    }

    # Return only keys we modify (for parallel state merge; no workflow_stage - both parallel nodes would conflict)
    return {
        "gap_analysis": gap_analysis,
        "matched_skills": matched,
        "missing_keywords": missing,
        "audit_log": [audit_entry],
    }
