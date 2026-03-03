"""
FastAPI for RSMEcreator - Resume Tailoring API.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from rsmecreator.logging_config import get_logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from rsmecreator.graph import tailor_resume
from rsmecreator.utils.doc_parser import extract_text_from_file

# Path to standalone UI
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

logger = get_logger("api")
app = FastAPI(title="RSMEcreator API", version="0.1.0")


@app.on_event("startup")
def startup():
    logger.info("RSMEcreator API starting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)


class TailorRequest(BaseModel):
    resume: str
    job_description: str
    output_format: str = "markdown"


class TailorResponse(BaseModel):
    final_resume: str
    validation_passed: bool
    validation_notes: list
    gap_analysis: dict | None = None
    ats_score: int = 0
    ats_analytics: dict | None = None


@app.get("/")
def root():
    return {"service": "RSMEcreator API", "ui": "/ui", "docs": "/docs", "health": "/health"}


@app.get("/ui")
def ui():
    """Serve the standalone UI (same origin = no CORS issues)."""
    path = FRONTEND_DIR / "index-standalone.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(path)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rsmecreator"}


def _run_tailor(resume: str, jd: str, output_format: str = "markdown") -> TailorResponse:
    """Shared tailor logic."""
    result = tailor_resume(resume=resume, jd=jd, output_format=output_format)
    if result.get("error_message"):
        raise HTTPException(status_code=400, detail=result["error_message"])
    return TailorResponse(
        final_resume=result.get("final_resume", ""),
        validation_passed=result.get("validation_passed", False),
        validation_notes=result.get("validation_notes", []),
        gap_analysis=result.get("gap_analysis"),
        ats_score=result.get("ats_score", 0),
        ats_analytics=result.get("ats_analytics"),
    )


@app.post("/api/v1/tailor", response_model=TailorResponse)
def tailor(request: TailorRequest):
    """Tailor a resume to a job description."""
    start = time.perf_counter()
    logger.info("Tailor request | resume_len=%d | jd_len=%d", len(request.resume), len(request.job_description))
    try:
        result = _run_tailor(
            resume=request.resume,
            jd=request.job_description,
            output_format=request.output_format,
        )
        logger.info("Tailor completed | elapsed=%.2fs | ats_score=%s", time.perf_counter() - start, result.ats_score)
        return result
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Tailor error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tailor/upload", response_model=TailorResponse)
async def tailor_upload(
    resume_file: UploadFile | None = File(None),
    jd_file: UploadFile | None = File(None),
    resume: str = Form(""),
    job_description: str = Form(""),
    output_format: str = Form("markdown"),
):
    """Tailor resume from text and/or uploaded DOCX files. Use file upload OR paste text for each."""
    start = time.perf_counter()
    resume_text = resume.strip() if resume else ""
    jd_text = job_description.strip() if job_description else ""
    try:
        if resume_file:
            data = await resume_file.read()
            resume_text = extract_text_from_file(data, resume_file.filename or "resume.docx")
        if jd_file:
            data = await jd_file.read()
            jd_text = extract_text_from_file(data, jd_file.filename or "jd.docx")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not resume_text or not jd_text:
        raise HTTPException(status_code=400, detail="Provide both resume and job description (paste text or upload DOCX)")
    logger.info("Tailor upload | resume_len=%d | jd_len=%d", len(resume_text), len(jd_text))
    try:
        result = _run_tailor(resume=resume_text, jd=jd_text, output_format=output_format)
        logger.info("Tailor upload completed | elapsed=%.2fs | ats_score=%s", time.perf_counter() - start, result.ats_score)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Tailor upload error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
