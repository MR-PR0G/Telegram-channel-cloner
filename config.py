# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import os
from typing import Literal, List, Optional

API_ID: int = 0  # Fill with your Telegram API ID
API_HASH: str = ""  # Fill with your Telegram API HASH

# Proxy Configuration
USE_PROXY: bool = True  # Set to True to enable proxy
PROXY_HOST: str = "127.0.0.1"
PROXY_PORT: int = 2080
PROXY_USERNAME: Optional[str] = None
PROXY_PASSWORD: Optional[str] = None

# Human Behavior & Delay Jitter
ENABLE_RANDOM_DELAY: bool = False
MIN_DELAY: float = 0.2
MAX_DELAY: float = 0.8
DEFAULT_DELAY: float = 0.35

# Text Replacement & Cleaning
ENABLE_TEXT_REPLACEMENT: bool = False
AUTO_REPLACE_USERNAMES: bool = False
REPLACE_DICTIONARY: dict = {}
REMOVE_PATTERNS: List[str] = []

# Custom Header & Footer (Signatures)
CUSTOM_HEADER: str = ""
CUSTOM_FOOTER: str = ""

# Media Filtering & Limits
ALLOWED_MEDIA_TYPES: List[str] = [
    "text", "photo", "video", "voice", "audio", "gif", "sticker", "document", "location", "contact", "round_video"
]
MAX_FILE_SIZE_MB: float = 0.0

# Date & Message ID Range Filtering
MIN_MSG_ID: int = 0
MAX_MSG_ID: int = 0
START_DATE: Optional[str] = None
END_DATE: Optional[str] = None

# Forum Topics / Threads Support
SOURCE_TOPIC_ID: Optional[int] = None
DESTINATION_TOPIC_ID: Optional[int] = None

# Pinned Messages Synchronization
SYNC_PINNED_MESSAGES: bool = False

# Network & Resilience Settings
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