import os
from dotenv import load_dotenv

load_dotenv()

def get_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value