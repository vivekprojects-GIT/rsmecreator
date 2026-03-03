"""
Quick test for RSMEcreator - run from project root: python test_tailor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rsmecreator.graph import tailor_resume

SAMPLE_RESUME = """
John Doe
john.doe@email.com | (555) 123-4567

Professional Summary
Software engineer with 4 years of experience in Python and web development.
Worked on backend services and APIs.

Experience
Software Engineer at TechCo (2020-2024)
- Built REST APIs using Python and FastAPI
- Worked with Docker and AWS
- Improved system performance

Skills
Python, FastAPI, Docker, SQL, Git
"""

SAMPLE_JD = """
Senior Backend Engineer

Requirements:
- 5+ years Python
- Microservices, Kubernetes, AWS
- CI/CD pipelines
- Team leadership

Keywords: Python, Kubernetes, microservices, AWS, Terraform
"""

if __name__ == "__main__":
    print("Running RSMEcreator test...")
    result = tailor_resume(SAMPLE_RESUME, SAMPLE_JD)
    print("\n--- FINAL RESUME ---")
    print(result.get("final_resume", "No output"))
    print("\n--- VALIDATION ---")
    for n in result.get("validation_notes", []):
        print(f"  - {n}")
    if result.get("error_message"):
        print("ERROR:", result["error_message"])
