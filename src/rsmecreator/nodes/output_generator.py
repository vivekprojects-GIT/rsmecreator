"""
Output Generator Node

Assembles the final tailored resume in the requested format (Markdown by default).
"""

import json
from datetime import datetime
from ..state import ResumeState
from ..logging_config import get_logger

logger = get_logger("nodes.output_generator")


def _to_markdown(parsed: dict) -> str:
    """Convert parsed resume to Markdown."""
    lines = []

    name = parsed.get("name") or parsed.get("full_name") or "Candidate"
    email = parsed.get("email") or ""
    phone = parsed.get("phone") or ""
    if name or email or phone:
        lines.append(f"# {name}")
        if email:
            lines.append(f"**Email:** {email}")
        if phone:
            lines.append(f"**Phone:** {phone}")
        lines.append("")

    summary = parsed.get("summary") or parsed.get("professional_summary")
    if summary:
        lines.append("## Professional Summary")
        if isinstance(summary, list):
            summary = " ".join(str(s) for s in summary)
        lines.append(str(summary))
        lines.append("")

    experience = parsed.get("experience") or parsed.get("work_experience") or []
    if experience:
        lines.append("## Experience")
        for exp in experience:
            if isinstance(exp, dict):
                company = exp.get("company") or exp.get("employer") or "Company"
                role = exp.get("role") or exp.get("title") or "Role"
                dates = exp.get("dates") or exp.get("duration") or ""
                lines.append(f"### {role} at {company}")
                if dates:
                    lines.append(f"*{dates}*")
                bullets = exp.get("bullets") or exp.get("achievements") or []
                for b in bullets:
                    lines.append(f"- {b}")
                lines.append("")
            else:
                lines.append(f"- {exp}")
        lines.append("")

    skills = parsed.get("skills") or []
    if skills:
        lines.append("## Skills")
        if isinstance(skills, list):
            lines.append(", ".join(str(s) for s in skills))
        else:
            lines.append(str(skills))
        lines.append("")

    education = parsed.get("education") or []
    if education:
        lines.append("## Education")
        for edu in education:
            if isinstance(edu, dict):
                school = edu.get("school") or edu.get("institution") or "Institution"
                degree = edu.get("degree") or ""
                lines.append(f"- {degree} - {school}")
            else:
                lines.append(f"- {edu}")
        lines.append("")

    certs = parsed.get("certifications") or []
    if certs:
        lines.append("## Certifications")
        for c in certs:
            lines.append(f"- {c}")
        lines.append("")

    return "\n".join(lines).strip()


def output_generator_node(state: ResumeState) -> ResumeState:
    """Generate final resume output."""
    parsed_resume = state.get("parsed_resume", {})
    output_format = state.get("output_format", "markdown")

    final_resume = _to_markdown(parsed_resume)
    logger.info("Output generated | len=%d chars", len(final_resume))

    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "output_generator",
        "output_format": output_format,
    }

    # Return only keys we modify (for parallel state merge)
    return {
        "final_resume": final_resume,
        "audit_log": [audit_entry],
    }
