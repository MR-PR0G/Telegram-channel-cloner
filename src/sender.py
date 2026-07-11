# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import config
from src.utils import apply_delay
from src.logger import get_logger

logger = get_logger()

async def send_message_safe(client: TelegramClient, entity, **kwargs) -> any:
    retries = 0
    if config.DESTINATION_TOPIC_ID and ('reply_to' not in kwargs or kwargs.get('reply_to') is None):
        kwargs['reply_to'] = config.DESTINATION_TOPIC_ID

    while retries <= config.MAX_RETRIES:
        try:
            sent_msg = await client.send_message(entity, **kwargs)
            await apply_delay()
            return sent_msg
        except FloodWaitError as e:
            logger.warning(f"FloodWait encountered: Sleeping for {e.seconds} seconds.")
            print(f"\n[Flood Wait] Sleeping {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            continue
        except Exception as e:
            retries += 1
            logger.error(f"Error executing message transmission (Attempt {retries}/{config.MAX_RETRIES}): {e}")
            if retries > config.MAX_RETRIES:
                raise e
            await asyncio.sleep(1.0)

async def send_file_safe(client: TelegramClient, entity, file, **kwargs) -> any:
    retries = 0
    if config.DESTINATION_TOPIC_ID and ('reply_to' not in kwargs or kwargs.get('reply_to') is None):
        kwargs['reply_to'] = config.DESTINATION_TOPIC_ID

    while retries <= config.MAX_RETRIES:
        try:
            sent_msg = await client.send_file(entity, file, **kwargs)
            await apply_delay()
            return sent_msg
        except FloodWaitError as e:
            logger.warning(f"FloodWait encountered during file transmission: Sleeping for {e.seconds} seconds.")
            print(f"\n[Flood Wait] Sleeping {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            continue
        except Exception as e:
            retries += 1
            logger.error(f"Error executing file transmission (Attempt {retries}/{config.MAX_RETRIES}): {e}")
            if retries > config.MAX_RETRIES:
                raise e
            await asyncio.sleep(1.0)

async def pin_message_safe(client: TelegramClient, entity, message_id: int) -> None:
    if not config.SYNC_PINNED_MESSAGES:
        return
    retries = 0
    while retries <= config.MAX_RETRIES:
        try:
            await client.pin_message(entity, message_id, notify=False)
            await apply_delay()
            break
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Failed to pin message ID {message_id}: {e}")
            break