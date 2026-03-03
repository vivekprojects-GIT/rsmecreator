"""
JD Analyzer Node

Extracts and structures key requirements, keywords, and responsibilities from the Job Description.
"""

from datetime import datetime
from ..state import ResumeState
from ..logging_config import get_logger

logger = get_logger("nodes.jd_analyzer")


def jd_analyzer_node(state: ResumeState) -> ResumeState:
    """Enrich JD analysis - already partially done in input_parser."""
    parsed_jd = state.get("parsed_jd", {})
    jd_requirements = state.get("jd_requirements", [])
    jd_keywords = state.get("jd_keywords", [])
    jd_responsibilities = state.get("jd_responsibilities", [])

    # Ensure lists
    if not isinstance(jd_requirements, list):
        jd_requirements = [jd_requirements] if jd_requirements else []
    if not isinstance(jd_keywords, list):
        jd_keywords = [jd_keywords] if jd_keywords else []
    if not isinstance(jd_responsibilities, list):
        jd_responsibilities = [jd_responsibilities] if jd_responsibilities else []

    jd_analysis = {
        "requirements": jd_requirements,
        "keywords": jd_keywords,
        "responsibilities": jd_responsibilities,
        "keyword_count": len(jd_keywords),
        "requirement_count": len(jd_requirements),
    }

    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "jd_analyzer",
        "keyword_count": len(jd_keywords),
        "requirement_count": len(jd_requirements),
    }

    logger.info("JD analyzed | keywords=%d | requirements=%d", len(jd_keywords), len(jd_requirements))
    # Return only keys we modify (for parallel state merge; no workflow_stage - both parallel nodes would conflict)
    return {
        "jd_analysis": jd_analysis,
        "jd_requirements": jd_requirements,
        "jd_keywords": jd_keywords,
        "jd_responsibilities": jd_responsibilities,
        "audit_log": [audit_entry],
    }
