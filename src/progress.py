# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import os
from dataclasses import dataclass, asdict
from typing import Optional
import orjson
import config
from src.logger import get_logger

logger = get_logger()

@dataclass
class CloneProgress:
    source_id: int
    destination_id: int
    last_source_msg_id: int
    copied_count: int
    timestamp: float
    source_title: str
    destination_title: str

def save_progress(progress: CloneProgress) -> None:
    try:
        data = asdict(progress)
        with open(config.PROGRESS_FILE, "wb") as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")

def load_progress() -> Optional[CloneProgress]:
    if not os.path.exists(config.PROGRESS_FILE):
        return None
    try:
        with open(config.PROGRESS_FILE, "rb") as f:
            data = orjson.loads(f.read())
        return CloneProgress(**data)
    except Exception as e:
        logger.error(f"Failed to load progress: {e}")
        return None

def clear_progress() -> None:
    if os.path.exists(config.PROGRESS_FILE):
        try:
            os.remove(config.PROGRESS_FILE)
        except Exception as e:
            logger.error(f"Failed to delete progress file: {e}")

def log_failed_message(msg_id: int) -> None:
    failed_ids = []
    if os.path.exists(config.FAILED_LOG_FILE):
        try:
            with open(config.FAILED_LOG_FILE, "rb") as f:
                failed_ids = orjson.loads(f.read())
        except Exception:
            failed_ids = []
            
    if msg_id not in failed_ids:
        failed_ids.append(msg_id)
        
    try:
        with open(config.FAILED_LOG_FILE, "wb") as f:
            f.write(orjson.dumps(failed_ids))
    except Exception as e:
        logger.error(f"Failed to record failed message ID {msg_id}: {e}")

def get_failed_messages_count() -> int:
    if not os.path.exists(config.FAILED_LOG_FILE):
        return 0
    try:
        with open(config.FAILED_LOG_FILE, "rb") as f:
            data = orjson.loads(f.read())
            return len(data)
    except Exception:
        return 0

def clear_failed_messages() -> None:
    if os.path.exists(config.FAILED_LOG_FILE):
        try:
            os.remove(config.FAILED_LOG_FILE)
        except Exception as e:
            logger.error(f"Failed to clear failed messages log: {e}")