"""
State Management for RSMEcreator - Resume Tailoring Workflow

Central state structure that tracks:
- Resume and JD inputs
- Parsed/structured data
- Analysis results
- Tailored output
"""

from typing import TypedDict, Optional, Dict, Any, List, Annotated
from operator import add


class ResumeState(TypedDict, total=False):
    """
    Central state for the resume tailoring workflow.
    """

    # === INPUTS ===
    raw_resume: str
    raw_jd: str
    resume_format: str  # "pdf", "docx", "txt", "markdown"

    # === PARSED DATA ===
    parsed_resume: Dict[str, Any]  # Structured resume (sections, experience, skills)
    parsed_jd: Dict[str, Any]  # Structured JD (requirements, keywords, responsibilities)

    # === JD ANALYSIS ===
    jd_requirements: List[str]
    jd_keywords: List[str]
    jd_responsibilities: List[str]
    jd_analysis: Dict[str, Any]

    # === GAP ANALYSIS ===
    gap_analysis: Dict[str, Any]  # Strengths, gaps, improvement areas
    matched_skills: List[str]
    missing_keywords: List[str]

    # === TAILORING ===
    tailoring_strategy: Dict[str, Any]  # What to emphasize/rewrite
    tailored_sections: Dict[str, str]  # Rewritten sections
    final_resume: str
    output_format: str  # "markdown", "pdf", "docx"

    # === VALIDATION ===
    validation_passed: bool
    validation_notes: List[str]

    # === ATS SCORING ===
    ats_score: int  # 0-100
    ats_analytics: Dict[str, Any]  # Breakdown and suggestions

    # === METADATA ===
    audit_log: Annotated[List[Dict[str, Any]], add]  # Reducer for parallel node merge
    error_message: Optional[str]
    workflow_stage: str
