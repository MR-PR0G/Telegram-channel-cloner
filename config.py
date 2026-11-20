import os
from typing import Literal, List, Optional

API_ID: int = int(os.getenv("TELEGRAM_API_ID", "24292412"))
API_HASH: str = os.getenv("TELEGRAM_API_HASH", "91554b7905061c7e056bc852f80b6914")

USE_PROXY: bool = os.getenv("USE_PROXY", "True").lower() in ("1", "true", "yes")
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

ENABLE_TEXT_REPLACEMENT: bool = False
AUTO_REPLACE_USERNAMES: bool = False
REPLACE_DICTIONARY: dict = {}
REMOVE_PATTERNS: List[str] = []

CUSTOM_HEADER: str = ""
CUSTOM_FOOTER: str = ""

ALLOWED_MEDIA_TYPES: List[str] = [
    "text", "photo", "video", "voice", "audio", "gif", "sticker", "document", "location", "contact", "round_video"
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

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
