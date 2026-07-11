# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import random
import asyncio
import re
from datetime import datetime, timezone
from typing import Optional
import config

def format_timedelta(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

async def apply_delay() -> None:
    if config.ENABLE_RANDOM_DELAY:
        delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
    else:
        delay = config.DEFAULT_DELAY
    await asyncio.sleep(delay)

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

def is_date_in_range(msg_date: datetime) -> bool:
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
            end_dt = datetime.strptime(config.END_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc)
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