"""
Content Rewriter Node

Uses LLM to rewrite resume sections to match the JD.
Preserves facts - only rephrases and reorders.
"""

import json
from datetime import datetime
from ..state import ResumeState
from ..config import get_llm
from ..logging_config import get_logger

logger = get_logger("nodes.content_rewriter")


def _rewrite_section(section_name: str, content: str, instructions: str, llm) -> str:
    """Rewrite a single section."""
    prompt = f"""Rewrite this resume section to better match the job description.

SECTION: {section_name}
CURRENT CONTENT:
---
{content[:1500]}
---

INSTRUCTIONS: {instructions}

Rules:
- PRESERVE all facts, dates, company names, and achievements. Do NOT invent anything.
- Rephrase to use JD-relevant language and keywords naturally.
- Keep the same length or slightly expand if adding relevant context.
- Return ONLY the rewritten content, no labels or extra text.
"""
    try:
        resp = llm.invoke(prompt)
        return resp.content.strip()
    except Exception as e:
        logger.warning("Rewrite failed for %s: %s, keeping original", section_name, e)
        return content  # Fallback to original


def content_rewriter_node(state: ResumeState) -> ResumeState:
    """Rewrite resume sections based on tailoring strategy."""
    parsed_resume = state.get("parsed_resume", {})
    tailoring_strategy = state.get("tailoring_strategy", {})
    jd_keywords = state.get("jd_keywords", [])
    gap_analysis = state.get("gap_analysis", {})

    llm = get_llm()
    sections_to_rewrite = tailoring_strategy.get("sections_to_rewrite", ["summary", "experience", "skills"])
    keyword_injections = tailoring_strategy.get("keyword_injections", {})
    summary_angle = tailoring_strategy.get("summary_angle", "Highlight relevance to the role.")
    bullet_focus = tailoring_strategy.get("bullet_focus", ["emphasize impact"])

    tailored_sections = {}

    # Rewrite summary
    summary = parsed_resume.get("summary") or parsed_resume.get("professional_summary") or ""
    if summary and ("summary" in sections_to_rewrite or "professional_summary" in sections_to_rewrite):
        if isinstance(summary, list):
            summary = " ".join(str(s) for s in summary)
        kw = keyword_injections.get("summary", jd_keywords[:5])
        instructions = f"{summary_angle} Incorporate these keywords naturally: {kw}"
        tailored_sections["summary"] = _rewrite_section("Summary", summary, instructions, llm)

    # Rewrite experience
    experience = parsed_resume.get("experience") or parsed_resume.get("work_experience") or []
    if experience and "experience" in sections_to_rewrite:
        exp_str = json.dumps(experience, indent=2)[:4000]
        instructions = f"Rephrase bullets to: {bullet_focus}. Use JD keywords where relevant. Keep same JSON structure - return valid JSON array of experience objects."
        rewritten = _rewrite_section("Experience", exp_str, instructions, llm)
        try:
            parsed = json.loads(rewritten)
            tailored_sections["experience"] = parsed if isinstance(parsed, list) else experience
        except json.JSONDecodeError:
            # Keep original if LLM returns non-JSON
            tailored_sections["experience"] = experience

    # Rewrite skills
    skills = parsed_resume.get("skills") or []
    if skills and "skills" in sections_to_rewrite:
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        kw = keyword_injections.get("skills", jd_keywords[:10])
        instructions = f"Incorporate these keywords if relevant to candidate: {kw}. Keep only skills the candidate has. Order by relevance to JD."
        rewritten = _rewrite_section("Skills", skills_str, instructions, llm)
        if isinstance(rewritten, str):
            tailored_sections["skills"] = [s.strip() for s in rewritten.replace(",", ";").split(";") if s.strip()][:20]
        else:
            tailored_sections["skills"] = rewritten

    # Merge with original - only replace rewritten sections
    merged = dict(parsed_resume)
    for k, v in tailored_sections.items():
        merged[k] = v

    logger.info("Content rewritten | sections=%s", list(tailored_sections.keys()))
    audit_log = state.get("audit_log", [])
    audit_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "content_rewriter",
        "sections_rewritten": list(tailored_sections.keys()),
    })

    return {
        **state,
        "tailored_sections": tailored_sections,
        "parsed_resume": merged,
        "workflow_stage": "content_rewritten",
        "audit_log": audit_log,
    }
