import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# LLM Configuration (Cloud API for inference)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "")

# Embedding Configuration (Ollama local API, 0 Token)
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "local")  # local or cloud
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "ollama")
EMBEDDING_API_BASE_URL = os.getenv("EMBEDDING_API_BASE_URL", "http://127.0.0.1:11434/v1")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text")

# VLM Configuration
VLM_API_KEY = os.getenv("VLM_API_KEY", "")
VLM_API_BASE_URL = os.getenv("VLM_API_BASE_URL", "")
VLM_MODEL_NAME = os.getenv("VLM_MODEL_NAME", "")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "exam_copilot.db"))
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "data" / "vectors.db"))

# OCR Configuration
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "ch")
OCR_USE_GPU = os.getenv("OCR_USE_GPU", "false").lower() == "true"

# Detection Thresholds
SSIM_THRESHOLD = float(os.getenv("SSIM_THRESHOLD", "0.85"))
STATIC_DELAY_SECONDS = float(os.getenv("STATIC_DELAY_SECONDS", "1.0"))
FTS_MATCH_THRESHOLD = float(os.getenv("FTS_MATCH_THRESHOLD", "0.85"))
COSINE_SIMILARITY_THRESHOLD = float(os.getenv("COSINE_SIMILARITY_THRESHOLD", "0.88"))

# UI Configuration
WINDOW_OPACITY = float(os.getenv("WINDOW_OPACITY", "0.9"))
HUD_OPACITY = float(os.getenv("HUD_OPACITY", "0.9"))
HOTKEY_TOGGLE = os.getenv("HOTKEY_TOGGLE", "ctrl+shift+o")
HOTKEY_QUIT = os.getenv("HOTKEY_QUIT", "ctrl+shift+q")
HOTKEY_PANIC = os.getenv("HOTKEY_PANIC", "ctrl+shift+x")  # 老板键：紧急隐藏
HOTKEY_RECOGNIZE = os.getenv("HOTKEY_RECOGNIZE", "ctrl+shift+a")  # 单次识别触发

# Model Paths
EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", str(BASE_DIR / "models" / "m3e-nano"))
RAPID_OCR_MODEL_PATH = os.getenv("RAPID_OCR_MODEL_PATH", str(BASE_DIR / "models" / "rapidocr"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "app.log"))

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        BASE_DIR / "data",
        BASE_DIR / "models",
        BASE_DIR / "logs",
        BASE_DIR / "assets" / "icons",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()