import random
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
import config

def format_timedelta(seconds: float) -> str:
    hours, remainder = divmod(int(max(0.0, seconds)), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

async def apply_delay() -> None:
    if config.ENABLE_RANDOM_DELAY:
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
    else:
        delay = config.DEFAULT_DELAY
    await asyncio.sleep(delay)

def truncate_caption(text: Optional[str], max_length: int = 1024) -> Tuple[Optional[str], Optional[str]]:
    if not text or len(text) <= max_length:
        return text, None

    cutoff = max_length
    split_pos = text.rfind("\n", 0, cutoff)
    if split_pos == -1 or split_pos < (max_length // 2):
        split_pos = text.rfind(" ", 0, cutoff)
    if split_pos == -1 or split_pos < (max_length // 2):
        split_pos = cutoff

    head = text[:split_pos].rstrip()
    tail = text[split_pos:].lstrip()
    return head, tail

def process_text_content(
    text: Optional[str], 
    source_username: Optional[str] = None, 
    dest_username: Optional[str] = None
) -> Optional[str]:
    if not text:
        return text

    modified = text

    if config.ENABLE_TEXT_REPLACEMENT:
        if config.AUTO_REPLACE_USERNAMES and source_username and dest_username:
            src_tag = f"@{source_username.lstrip('@')}"
            dst_tag = f"@{dest_username.lstrip('@')}"
            modified = re.sub(re.escape(src_tag), dst_tag, modified, flags=re.IGNORECASE)

        for old_val, new_val in config.REPLACE_DICTIONARY.items():
            modified = modified.replace(old_val, new_val)

        for pattern in config.REMOVE_PATTERNS:
            modified = re.sub(pattern, "", modified, flags=re.IGNORECASE)

    if config.CUSTOM_HEADER:
        modified = f"{config.CUSTOM_HEADER}\n\n{modified}"

    if config.CUSTOM_FOOTER:
        modified = f"{modified}\n\n{config.CUSTOM_FOOTER}"

    return modified.strip()

def is_date_in_range(msg_date: Optional[datetime]) -> bool:
    if not msg_date:
        return True

    if config.START_DATE:
        try:
            start_dt = datetime.strptime(config.START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if msg_date < start_dt:
                return False
        except ValueError:
            pass

    if config.END_DATE:
        try:
            end_dt = datetime.strptime(config.END_DATE, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
            if msg_date > end_dt:
                return False
        except ValueError:
            pass

    return True

def is_media_allowed(media_type: str, file_size_bytes: int = 0) -> bool:
    if media_type not in config.ALLOWED_MEDIA_TYPES:
        return False

    if config.MAX_FILE_SIZE_MB > 0 and file_size_bytes > 0:
        max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_bytes:
            return False

    return True

def get_entity_display_name(entity) -> str:
    if not entity:
        return "Unknown"

    if getattr(entity, 'is_self', False) is True:
        return "Saved Messages"

    actual = getattr(entity, 'entity', None) or entity

    if getattr(actual, 'is_self', False) is True:
        return "Saved Messages"

    title = getattr(actual, 'title', None)
    if title:
        return str(title)

    first_name = getattr(actual, 'first_name', None) or ''
    last_name = getattr(actual, 'last_name', None) or ''
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name

    username = getattr(actual, 'username', None)
    if username:
        return f"@{username}"

    name = getattr(entity, 'name', None)
    if name:
        return str(name)

    return str(getattr(entity, 'id', 'Unknown'))

def get_entity_username(entity) -> str:
    if not entity:
        return ""
    actual = getattr(entity, 'entity', entity)
    return getattr(actual, 'username', '') or ''
