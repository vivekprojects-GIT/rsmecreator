"""
Configuration for RSMEcreator.
"""

import os
from dotenv import load_dotenv

from .logging_config import get_logger

load_dotenv()
logger = get_logger("config")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, google
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:120b-cloud")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")  # for future RAG/semantic features
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


def get_llm():
    """Get LLM instance based on configured provider."""
    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        logger.info("Using OpenAI LLM: %s", LLM_MODEL or "gpt-4o-mini")
        return ChatOpenAI(model=LLM_MODEL or "gpt-4o-mini", temperature=0.3)
    if LLM_PROVIDER == "google" and GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info("Using Google LLM: %s", LLM_MODEL or "gemini-pro")
        return ChatGoogleGenerativeAI(model=LLM_MODEL or "gemini-pro", temperature=0.3)
    # Default: Ollama (local)
    from langchain_ollama import ChatOllama
    logger.info("Using Ollama LLM: %s", LLM_MODEL)
    return ChatOllama(model=LLM_MODEL, temperature=0.3)
