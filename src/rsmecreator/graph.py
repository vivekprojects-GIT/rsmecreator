"""
LangGraph Workflow for RSMEcreator - Resume Tailoring (Parallel)

Flow:
  input_parser → [on error] END
  input_parser → [on success] jd_analyzer ──┐
                         gap_analyzer ────┴─→ tailoring_planner → content_rewriter
                                                                      ├─→ validator ────┐
                                                                      └─→ output_generator ┘
                                                                                    ↓
                                                                              ats_scorer → END
"""

from typing import Literal, Union
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from .state import ResumeState
from .logging_config import get_logger
from .nodes import (
    input_parser_node,
    jd_analyzer_node,
    gap_analyzer_node,
    tailoring_planner_node,
    content_rewriter_node,
    validator_node,
    output_generator_node,
    ats_scorer_node,
)

logger = get_logger("graph")


def _route_after_parser(state: ResumeState) -> Union[Literal["end"], list[Send]]:
    """Route to end if parsing failed, else fan out to jd_analyzer and gap_analyzer in parallel."""
    if state.get("error_message"):
        logger.warning("Parse failed, routing to END: %s", state.get("error_message"))
        return END
    logger.debug("Routing to parallel: jd_analyzer, gap_analyzer")
    return [Send("jd_analyzer", state), Send("gap_analyzer", state)]


def _route_after_content_rewriter(state: ResumeState) -> list[Send]:
    """Fan out to validator and output_generator in parallel."""
    return [Send("validator", state), Send("output_generator", state)]


def build_resume_graph():
    """Build and compile the resume tailoring graph with parallel execution."""
    workflow = StateGraph(ResumeState)

    workflow.add_node("input_parser", input_parser_node)
    workflow.add_node("jd_analyzer", jd_analyzer_node)
    workflow.add_node("gap_analyzer", gap_analyzer_node)
    workflow.add_node("tailoring_planner", tailoring_planner_node)
    workflow.add_node("content_rewriter", content_rewriter_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("output_generator", output_generator_node)
    workflow.add_node("ats_scorer", ats_scorer_node)

    workflow.set_entry_point("input_parser")
    workflow.add_conditional_edges("input_parser", _route_after_parser)

    # Parallel: jd_analyzer and gap_analyzer both → tailoring_planner (join)
    workflow.add_edge("jd_analyzer", "tailoring_planner")
    workflow.add_edge("gap_analyzer", "tailoring_planner")

    workflow.add_edge("tailoring_planner", "content_rewriter")
    workflow.add_conditional_edges("content_rewriter", _route_after_content_rewriter)

    # Parallel: validator and output_generator both → ats_scorer (join)
    workflow.add_edge("validator", "ats_scorer")
    workflow.add_edge("output_generator", "ats_scorer")

    workflow.add_edge("ats_scorer", END)

    return workflow.compile()


def tailor_resume(resume: str, jd: str, output_format: str = "markdown") -> dict:
    """Convenience function to run the full tailoring workflow."""
    logger.info("Starting resume tailoring (output_format=%s)", output_format)
    graph = build_resume_graph()
    initial_state: ResumeState = {
        "raw_resume": resume,
        "raw_jd": jd,
        "output_format": output_format,
        "audit_log": [],
    }
    final_state = graph.invoke(initial_state)
    err = final_state.get("error_message")
    if err:
        logger.warning("Workflow completed with error: %s", err)
    else:
        ats = final_state.get("ats_score", 0)
        logger.info("Workflow completed | ATS score=%s | validation_passed=%s",
                    ats, final_state.get("validation_passed"))
    return dict(final_state)
