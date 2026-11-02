"""Environment configuration. Never place API keys in source code."""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

@lru_cache
def agent_mode() -> str:
    mode = os.getenv("AGENT_MODE", "demo").lower().strip()
    if mode not in {"demo", "ai"}:
        raise ValueError("AGENT_MODE must be 'demo' or 'ai'")
    return mode

def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
