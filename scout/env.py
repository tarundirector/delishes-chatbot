from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.


SUPABASE_URL=os.getenv("SUPABASE_URL", None)
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", None)
LANGSMITH_API_KEY=os.getenv("LANGSMITH_API_KEY", None)
REDIS_URI=os.getenv("REDIS_URI", None)
DATABASE_URI=os.getenv("DATABASE_URI", None)


required_env_vars = {
    "SUPABASE_URL": SUPABASE_URL,
    "OPENAI_API_KEY": OPENAI_API_KEY,
}

for name, value in required_env_vars.items():
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")