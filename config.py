import os
from typing import Literal, List, Optional

def _load_env_file():
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
        except Exception:
            pass

_load_env_file()

API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")

USE_PROXY: bool = os.getenv("USE_PROXY", "False").lower() in ("1", "true", "yes")
PROXY_TYPE: Literal["HTTP", "SOCKS5", "SOCKS4"] = os.getenv("PROXY_TYPE", "HTTP").upper()
PROXY_HOST: str = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT: int = int(os.getenv("PROXY_PORT", "2080"))
PROXY_USERNAME: Optional[str] = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD: Optional[str] = os.getenv("PROXY_PASSWORD")

ENABLE_RANDOM_DELAY: bool = True
MIN_DELAY: float = 0.3
MAX_DELAY: float = 1.0
DEFAULT_DELAY: float = 0.4

BATCH_SIZE: int = 100
BATCH_COOLDOWN_SECONDS: float = 0.0

MAX_CAPTION_LENGTH: int = 1024
SPLIT_LONG_CAPTION: bool = True
BYPASS_RESTRICTED_MEDIA: bool = True

ENABLE_TEXT_REPLACEMENT: bool = False
AUTO_REPLACE_USERNAMES: bool = False
REPLACE_DICTIONARY: dict = {}
REMOVE_PATTERNS: List[str] = []

CUSTOM_HEADER: str = ""
CUSTOM_FOOTER: str = ""

ALLOWED_MEDIA_TYPES: List[str] = [
    "text", "webpage", "photo", "video", "voice", "audio", "gif", "sticker", "document", "location", "contact", "round_video", "poll", "dice"
]
MAX_FILE_SIZE_MB: float = 0.0

MIN_MSG_ID: int = 0
MAX_MSG_ID: int = 0
START_DATE: Optional[str] = None
END_DATE: Optional[str] = None

SOURCE_TOPIC_ID: Optional[int] = None
DESTINATION_TOPIC_ID: Optional[int] = None

SYNC_PINNED_MESSAGES: bool = False

LOG_LEVEL: Literal["INFO", "WARNING", "ERROR", "DEBUG"] = "INFO"
AUTO_RESUME: bool = False
MAX_RETRIES: int = 3
NETWORK_TIMEOUT: int = 10
NETWORK_RETRIES: int = 3

SESSION_DIR: str = "session"
PROGRESS_FILE: str = "progress.json"
FAILED_LOG_FILE: str = "failed_messages.json"
LOG_DIR: str = "logs"
TEMP_DOWNLOAD_DIR: str = "temp_downloads"

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
