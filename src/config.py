import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INDEX_DIR = DATA_DIR / "faiss_index"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "openai/gpt-oss-120b"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

TOP_K = 5
THRESHOLD = 0.30

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_PROVIDER = "groq"

# LLM_PROVIDER = "gemini"
# GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
