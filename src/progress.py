import os
from dataclasses import dataclass, asdict
from typing import Optional, List
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

def load_failed_messages() -> List[int]:
    if not os.path.exists(config.FAILED_LOG_FILE):
        return []
    try:
        with open(config.FAILED_LOG_FILE, "rb") as f:
            raw_data = orjson.loads(f.read())
        if isinstance(raw_data, list):
            result = []
            for item in raw_data:
                if isinstance(item, int):
                    result.append(item)
                elif isinstance(item, dict) and "id" in item:
                    result.append(int(item["id"]))
            return sorted(list(set(result)))
        return []
    except Exception as e:
        logger.error(f"Failed reading failed messages file: {e}")
        return []

def save_failed_messages(msg_ids: List[int]) -> None:
    unique_sorted = sorted(list(set(msg_ids)))
    try:
        if not unique_sorted:
            clear_failed_messages()
            return
        with open(config.FAILED_LOG_FILE, "wb") as f:
            f.write(orjson.dumps(unique_sorted, option=orjson.OPT_INDENT_2))
    except Exception as e:
        logger.error(f"Failed writing failed messages: {e}")

def log_failed_message(msg_id: int) -> None:
    current_ids = load_failed_messages()
    if msg_id not in current_ids:
        current_ids.append(msg_id)
        save_failed_messages(current_ids)

def remove_failed_message(msg_id: int) -> None:
    current_ids = load_failed_messages()
    if msg_id in current_ids:
        current_ids.remove(msg_id)
        save_failed_messages(current_ids)

def remove_failed_messages(msg_ids: List[int]) -> None:
    target_set = set(msg_ids)
    current_ids = [mid for mid in load_failed_messages() if mid not in target_set]
    save_failed_messages(current_ids)

def get_failed_messages_count() -> int:
    return len(load_failed_messages())

def clear_failed_messages() -> None:
    if os.path.exists(config.FAILED_LOG_FILE):
        try:
            os.remove(config.FAILED_LOG_FILE)
        except Exception as e:
            logger.error(f"Failed to clear failed messages log: {e}")
