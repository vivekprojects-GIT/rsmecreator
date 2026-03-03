"""
ATS (Applicant Tracking System) Scorer Node

Computes ATS compatibility score and analytics for the tailored resume.
"""

import re
from datetime import datetime
from ..state import ResumeState
from ..logging_config import get_logger

logger = get_logger("nodes.ats_scorer")


# Common action verbs that strengthen resume bullets
ACTION_VERBS = {
    "achieved", "managed", "led", "developed", "implemented", "created",
    "designed", "built", "improved", "increased", "reduced", "optimized",
    "automated", "launched", "delivered", "established", "drove", "executed",
    "coordinated", "analyzed", "resolved", "streamlined", "transformed",
}


def _score_keyword_match(resume_text: str, keywords: list) -> tuple[int, float, list, list]:
    """Score 0-30 for keyword coverage."""
    resume_lower = resume_text.lower()
    matched = []
    missing = []
    for kw in keywords[:25]:
        if not isinstance(kw, str):
            continue
        kw_lower = kw.lower()
        if kw_lower in resume_lower or any(kw_lower in w for w in resume_lower.split()):
            matched.append(kw)
        else:
            missing.append(kw)
    total = max(len(keywords[:25]), 1)
    pct = len(matched) / total
    score = int(min(30, pct * 30))
    return score, pct, matched, missing


def _score_sections(parsed: dict) -> tuple[int, dict]:
    """Score 0-25 for section completeness."""
    sections = {"summary": 5, "experience": 8, "skills": 6, "education": 4, "certifications": 2}
    present = {}
    total = 0
    for sec, pts in sections.items():
        val = parsed.get(sec) or parsed.get(f"{sec}s") or parsed.get("work_experience" if sec == "experience" else sec)
        if val and (isinstance(val, list) and len(val) > 0 or isinstance(val, str) and len(val) > 10):
            present[sec] = True
            total += pts
        else:
            present[sec] = False
    return min(25, total), present


def _score_formatting(final_resume: str) -> tuple[int, list]:
    """Score 0-20 for formatting (headers, bullets, structure)."""
    score = 0
    notes = []
    lines = [l.strip() for l in final_resume.split("\n") if l.strip()]
    has_h1 = any(l.startswith("# ") for l in lines)
    has_h2 = sum(1 for l in lines if l.startswith("## "))
    has_bullets = sum(1 for l in lines if l.startswith("- ") or re.match(r"^[\*•]\s", l))
    if has_h1:
        score += 5
    else:
        notes.append("Add a clear name/header")
    if has_h2 >= 2:
        score += 8
    elif has_h2 >= 1:
        score += 4
    if has_bullets >= 3:
        score += 7
    elif has_bullets >= 1:
        score += 3
    return min(20, score), notes


def _score_action_verbs(resume_text: str) -> tuple[int, int]:
    """Score 0-15 for action verbs and quantified results."""
    words = resume_text.lower().split()
    action_count = sum(1 for w in words if w.rstrip("s") in ACTION_VERBS or w in ACTION_VERBS)
    has_numbers = bool(re.search(r"\d+%|\d+x|\$[\d,]+|\d+\+|\d+ years?", resume_text, re.I))
    score = min(10, action_count // 2) + (5 if has_numbers else 0)
    return min(15, score), action_count


def _score_length(final_resume: str) -> int:
    """Score 0-10 for appropriate length (not too short, not too long)."""
    word_count = len(final_resume.split())
    if 300 <= word_count <= 800:
        return 10
    if 200 <= word_count < 300 or 800 < word_count <= 1200:
        return 7
    if 100 <= word_count < 200 or 1200 < word_count <= 1500:
        return 5
    return 2


def ats_scorer_node(state: ResumeState) -> ResumeState:
    """Compute ATS score and analytics."""
    final_resume = state.get("final_resume", "")
    parsed_resume = state.get("parsed_resume", {})
    jd_keywords = state.get("jd_keywords", [])
    gap_analysis = state.get("gap_analysis", {})

    if not final_resume:
        logger.warning("ATS scorer: no resume to score")
        audit_log = state.get("audit_log", [])
        audit_log.append({"timestamp": datetime.utcnow().isoformat(), "action": "ats_scorer", "ats_score": 0})
        return {
            **state,
            "ats_score": 0,
            "ats_analytics": {"error": "No resume to score"},
            "audit_log": audit_log,
        }

    resume_text = final_resume + " " + str(parsed_resume)

    # Component scores (total 100)
    kw_score, kw_pct, matched, missing = _score_keyword_match(resume_text, jd_keywords)
    sec_score, sec_present = _score_sections(parsed_resume)
    fmt_score, fmt_notes = _score_formatting(final_resume)
    act_score, act_count = _score_action_verbs(resume_text)
    len_score = _score_length(final_resume)

    total_score = kw_score + sec_score + fmt_score + act_score + len_score

    suggestions = []
    if missing[:5]:
        suggestions.append(f"Add these keywords: {', '.join(missing[:5])}")
    for sec, ok in sec_present.items():
        if not ok:
            suggestions.append(f"Include a {sec} section")
    suggestions.extend(fmt_notes)
    if act_count < 3:
        suggestions.append("Use more action verbs (e.g., led, developed, achieved)")
    if not re.search(r"\d+", final_resume):
        suggestions.append("Add quantified results (%, numbers, metrics)")

    ats_analytics = {
        "total_score": total_score,
        "breakdown": {
            "keyword_match": {"score": kw_score, "max": 30, "percentage": round(kw_pct * 100, 1), "matched": matched[:10], "missing": missing[:5]},
            "sections": {"score": sec_score, "max": 25, "present": sec_present},
            "formatting": {"score": fmt_score, "max": 20},
            "action_verbs": {"score": act_score, "max": 15, "count": act_count},
            "length": {"score": len_score, "max": 10, "word_count": len(final_resume.split())},
        },
        "suggestions": suggestions[:6],
        "grade": "A" if total_score >= 80 else "B" if total_score >= 65 else "C" if total_score >= 50 else "D",
    }

    logger.info("ATS scored | score=%d | grade=%s", total_score, ats_analytics["grade"])
    audit_log = state.get("audit_log", [])
    audit_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "ats_scorer",
        "ats_score": total_score,
    })

    return {
        **state,
        "ats_score": total_score,
        "ats_analytics": ats_analytics,
        "workflow_stage": "complete",
        "audit_log": audit_log,
    }
