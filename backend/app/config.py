import os
from dotenv import load_dotenv

# Load values from .env if present
load_dotenv()

APP_NAME: str = os.getenv("APP_NAME", "Personalised Travel Planner")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Supabase database configuration (optional; falls back to in-memory store if absent)
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", ""))

# AI provider configuration (groq, gemini, openai, or mock)
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq").lower()
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
AI_API_KEY: str = os.getenv("AI_API_KEY", GROQ_API_KEY or GEMINI_API_KEY or OPENAI_API_KEY)
AI_MODEL: str = os.getenv("AI_MODEL", "")
LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "45"))

# Default currency
DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
