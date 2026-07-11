# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

from telethon import TelegramClient
from telethon.tl.types import MessageService
import config
from src.media import determine_media_attributes
from src.utils import process_text_content, is_date_in_range, is_media_allowed
from src.sender import send_message_safe, send_file_safe, pin_message_safe
from src.logger import get_logger

logger = get_logger()

async def process_single_message(
    client: TelegramClient, 
    message, 
    destination_id: int, 
    reply_mapping: dict,
    source_username: str = "",
    dest_username: str = ""
) -> bool:
    if isinstance(message, MessageService):
        logger.info(f"Skipping service message ID: {message.id}")
        return False

    if not is_date_in_range(message.date):
        logger.info(f"Skipping message ID {message.id} due to date filter constraint.")
        return False

    if config.MIN_MSG_ID > 0 and message.id < config.MIN_MSG_ID:
        return False
    if config.MAX_MSG_ID > 0 and message.id > config.MAX_MSG_ID:
        return False

    media_type, file_size = determine_media_attributes(message.media)
    if not is_media_allowed(media_type, file_size):
        logger.info(f"Skipping message ID {message.id} due to media filter ({media_type}, size: {file_size}).")
        return False

    processed_text = process_text_content(
        message.message, 
        source_username=source_username, 
        dest_username=dest_username
    )

    reply_to_id = None
    if message.reply_to and message.reply_to.reply_to_msg_id:
        old_reply_id = message.reply_to.reply_to_msg_id
        reply_to_id = reply_mapping.get(old_reply_id)

    try:
        sent_msg = None

        if message.media:
            if media_type in ["photo", "video", "voice", "audio", "gif", "sticker", "document", "round_video"]:
                sent_msg = await send_file_safe(
                    client, destination_id, message.media,
                    caption=processed_text, reply_to=reply_to_id
                )
            elif media_type in ["location", "contact"]:
                sent_msg = await send_message_safe(
                    client, destination_id, message=message.media, reply_to=reply_to_id
                )
            else:
                sent_msg = await send_message_safe(
                    client, destination_id, message=processed_text, reply_to=reply_to_id
                )
        else:
            if processed_text or message.entities:
                sent_msg = await send_message_safe(
                    client, destination_id, message=processed_text,
                    formatting_entities=message.entities, reply_to=reply_to_id
                )

        if sent_msg:
            reply_mapping[message.id] = sent_msg.id

            if getattr(message, 'pinned', False) and config.SYNC_PINNED_MESSAGES:
                await pin_message_safe(client, destination_id, sent_msg.id)

            return True

        return False

    except Exception as e:
        logger.error(f"Critical mapping crash dealing with message ID {message.id}: {e}")
        raise e