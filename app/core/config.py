from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "").rstrip("/")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")
groq_client = Groq(api_key=GROQ_API_KEY)
