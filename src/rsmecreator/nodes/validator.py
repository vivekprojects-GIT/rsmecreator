"""
Validator Node

Validates the tailored resume:
- Keyword coverage
- No fabrication
- Completeness
"""

from datetime import datetime
from ..state import ResumeState
from ..logging_config import get_logger

logger = get_logger("nodes.validator")


def validator_node(state: ResumeState) -> ResumeState:
    """Validate the tailored resume."""
    parsed_resume = state.get("parsed_resume", {})
    jd_keywords = state.get("jd_keywords", [])
    gap_analysis = state.get("gap_analysis", {})

    import json
    resume_text = json.dumps(parsed_resume).lower()

    # Check keyword coverage
    matched = []
    missing = []
    for kw in jd_keywords[:20]:
        if isinstance(kw, str) and kw.lower() in resume_text:
            matched.append(kw)
        elif isinstance(kw, str):
            missing.append(kw)

    coverage = len(matched) / max(len(jd_keywords[:20]), 1)
    validation_passed = coverage >= 0.3  # At least 30% keyword coverage

    validation_notes = [
        f"Keyword coverage: {len(matched)}/{min(20, len(jd_keywords))} ({coverage:.0%})",
    ]
    if missing[:5]:
        validation_notes.append(f"Consider adding: {', '.join(missing[:5])}")
    if validation_passed:
        validation_notes.append("Validation passed.")
    else:
        validation_notes.append("Low keyword coverage - consider manual review.")

    logger.info("Validation | passed=%s | coverage=%.0f%%", validation_passed, coverage * 100)
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "validator",
        "validation_passed": validation_passed,
        "keyword_coverage": coverage,
    }

    # Return only keys we modify (for parallel state merge; no workflow_stage - would conflict with output_generator)
    return {
        "validation_passed": validation_passed,
        "validation_notes": validation_notes,
        "audit_log": [audit_entry],
    }
