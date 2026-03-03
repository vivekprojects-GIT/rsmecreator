"""
Tailoring Planner Node

Creates a strategy for how to tailor the resume:
- Which sections to rewrite
- What to emphasize
- Order of sections
"""

import json
from datetime import datetime
from ..state import ResumeState
from ..config import get_llm
from ..logging_config import get_logger

logger = get_logger("nodes.tailoring_planner")


def tailoring_planner_node(state: ResumeState) -> ResumeState:
    """Plan the tailoring strategy based on gap analysis."""
    parsed_resume = state.get("parsed_resume", {})
    gap_analysis = state.get("gap_analysis", {})
    jd_keywords = state.get("jd_keywords", [])
    jd_requirements = state.get("jd_requirements", [])

    suggestions = gap_analysis.get("suggestions", [])
    emphasize = gap_analysis.get("emphasize", [])
    missing = gap_analysis.get("missing_keywords", [])

    llm = get_llm()
    prompt = f"""Create a tailoring plan for this resume to match the job description.

RESUME SECTIONS: {list(parsed_resume.keys()) if isinstance(parsed_resume, dict) else 'unknown'}
GAP ANALYSIS: strengths={gap_analysis.get('strengths', [])[:3]}, gaps={gap_analysis.get('gaps', [])[:5]}
MISSING KEYWORDS: {missing[:10]}
SUGGESTIONS: {suggestions[:5]}

Return JSON:
- sections_to_rewrite: list of section names to rewrite (e.g., summary, experience, skills)
- section_priorities: which sections to put first (reorder for impact)
- keyword_injections: dict of section -> list of keywords to naturally incorporate
- bullet_focus: for experience, which bullet points to enhance (by index or theme)
- summary_angle: 1-2 sentence guidance for the new summary

Return ONLY valid JSON. No markdown.
JSON:"""
    try:
        resp = llm.invoke(prompt)
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        tailoring_strategy = json.loads(content)
    except Exception as e:
        logger.warning("LLM tailoring plan failed, using fallback: %s", e)
        tailoring_strategy = {
            "sections_to_rewrite": ["summary", "experience", "skills"],
            "section_priorities": ["summary", "experience", "skills", "education"],
            "keyword_injections": {"skills": missing[:5], "summary": missing[:3]},
            "bullet_focus": ["emphasize results", "add metrics", "match JD language"],
            "summary_angle": "Reframe to highlight relevant experience for this role.",
        }

    logger.info("Tailoring planned | sections_to_rewrite=%s", tailoring_strategy.get("sections_to_rewrite", []))
    audit_log = state.get("audit_log", [])
    audit_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "tailoring_planner",
        "sections_to_rewrite": tailoring_strategy.get("sections_to_rewrite", []),
    })

    return {
        **state,
        "tailoring_strategy": tailoring_strategy,
        "workflow_stage": "tailoring_planned",
        "audit_log": audit_log,
    }
