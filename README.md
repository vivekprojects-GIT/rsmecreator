# RSMEcreator

**Agentic AI Resume Tailoring Application** – Tailors your resume to any job description using LangGraph.

## Features

- **Input**: Resume (plain text) + Job Description
- **Output**: Tailored resume in Markdown
- **Flow**: Parse → Analyze JD → Gap Analysis → Tailoring Plan → Content Rewrite → Validate → Output

## Setup

```bash
cd rsmecreator
pip install -r requirements.txt
cp .env.example .env
# Edit .env if using OpenAI or Google (default: Ollama)
```

### Ollama (Local, default)

```bash
ollama pull llama3.2
```

## Run

### 1. Start the API (required)

```bash
uvicorn api.main:app --reload --port 8000
```

Or on Windows: `run_api.bat`

### 2. Start the React frontend

```bash
cd frontend
npm install
npm run dev
```

Or on Windows: `run_frontend.bat`

The app will be at http://localhost:5173 (proxies API requests to port 8000).

**POST /api/v1/tailor**

```json
{
  "resume": "Your resume text...",
  "job_description": "Job description text...",
  "output_format": "markdown"
}
```

## Logging

Logs go to console and optionally to `logs/rsmecreator.log`. Configure via `.env`:

```
LOG_LEVEL=INFO      # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE=true    # Set false to disable file logging
```

## Project Structure

```
rsmecreator/
├── src/rsmecreator/      # LangGraph backend
│   ├── state.py
│   ├── graph.py
│   ├── config.py
│   ├── logging_config.py
│   └── nodes/
├── api/main.py           # FastAPI (CORS enabled for React)
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   └── package.json
└── requirements.txt
```

## LangGraph Flow

```
input_parser → jd_analyzer → gap_analyzer → tailoring_planner
  → content_rewriter → validator → output_generator → END
```
