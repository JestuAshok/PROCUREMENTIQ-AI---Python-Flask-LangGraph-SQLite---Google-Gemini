import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'procurementiq-super-secure-session-key-2026')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'instance' / 'procurementiq.db'))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'csv'}
    
    # LLM configuration
    DEMO_MODE = os.environ.get('DEMO_MODE', 'true').lower() in ('true', '1', 't')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'gemini')  # 'gemini', 'openai', 'groq', or 'demo'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY', '')
    NGROK_API_KEY = os.environ.get('NGROK_API_KEY', '')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

    # Scoring Weights Defaults
    DEFAULT_WEIGHTS = {
        'cost': 0.40,
        'delivery': 0.25,
        'risk': 0.20,
        'warranty': 0.15
    }
