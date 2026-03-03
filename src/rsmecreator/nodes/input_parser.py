"""
Input Parser Node

Parses raw resume and JD text into structured format.
Handles PDF, DOCX, TXT, and Markdown input.
"""

import json
from datetime import datetime
from ..state import ResumeState
from ..config import get_llm
from ..logging_config import get_logger

logger = get_logger("nodes.input_parser")


def _parse_with_llm(text: str, label: str) -> dict:
    """Use LLM to structure text into JSON."""
    llm = get_llm()
    prompt = f"""Parse the following {label} into a structured JSON format.
Extract: name, email, phone, summary, experience (list of {{company, role, dates, bullets}}),
skills (list), education (list), certifications (list).
If a field is not present, use null or empty list.
Return ONLY valid JSON, no markdown or extra text.

{label}:
---
{text[:8000]}
---

JSON:"""
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        logger.warning("LLM parse failed for %s: %s", label, e)
        return {"raw": text[:2000], "parse_error": str(e)}


def input_parser_node(state: ResumeState) -> ResumeState:
    """Parse resume and JD into structured format."""
    raw_resume = state.get("raw_resume", "")
    raw_jd = state.get("raw_jd", "")
    logger.debug("Parsing resume (%d chars) and JD (%d chars)", len(raw_resume), len(raw_jd))

    if not raw_resume or not raw_jd:
        logger.warning("Missing input: resume=%s jd=%s", bool(raw_resume), bool(raw_jd))
        return {
            **state,
            "error_message": "Both resume and job description are required.",
            "workflow_stage": "parse_failed",
        }

    # Parse resume
    parsed_resume = _parse_with_llm(raw_resume, "RESUME")

    # Parse JD - simpler structure
    llm = get_llm()
    jd_prompt = f"""Extract from this Job Description:
1. requirements: list of key requirements (skills, years of experience, qualifications)
2. keywords: list of important keywords to include in a resume
3. responsibilities: list of key job responsibilities

Return ONLY valid JSON. No markdown.

Job Description:
---
{raw_jd[:6000]}
---

JSON:"""
    try:
        jd_response = llm.invoke(jd_prompt)
        jd_content = jd_response.content.strip()
        if jd_content.startswith("```"):
            jd_content = jd_content.split("```")[1]
            if jd_content.startswith("json"):
                jd_content = jd_content[4:]
        parsed_jd = json.loads(jd_content)
    except Exception as e:
        logger.warning("JD parse failed: %s", e)
        parsed_jd = {"raw": raw_jd[:2000], "requirements": [], "keywords": [], "responsibilities": []}

    logger.info("Input parsed | resume_sections=%s | jd_keywords=%d", list(parsed_resume.keys()) if isinstance(parsed_resume, dict) else [], len(parsed_jd.get("keywords", [])) if isinstance(parsed_jd, dict) else 0)
    audit_log = state.get("audit_log", [])
    audit_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "input_parser",
        "resume_sections": list(parsed_resume.keys()) if isinstance(parsed_resume, dict) else [],
        "jd_keys": list(parsed_jd.keys()) if isinstance(parsed_jd, dict) else [],
    })

    return {
        **state,
        "parsed_resume": parsed_resume,
        "parsed_jd": parsed_jd,
        "jd_requirements": parsed_jd.get("requirements", []) if isinstance(parsed_jd, dict) else [],
        "jd_keywords": parsed_jd.get("keywords", []) if isinstance(parsed_jd, dict) else [],
        "jd_responsibilities": parsed_jd.get("responsibilities", []) if isinstance(parsed_jd, dict) else [],
        "workflow_stage": "parsed",
        "audit_log": audit_log,
    }
