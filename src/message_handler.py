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
        return False

    if not is_date_in_range(message.date):
        return False

    if config.MIN_MSG_ID > 0 and message.id < config.MIN_MSG_ID:
        return False
    if config.MAX_MSG_ID > 0 and message.id > config.MAX_MSG_ID:
        return False

    media_type, file_size = determine_media_attributes(message.media)
    if not is_media_allowed(media_type, file_size):
        return False

    raw_text = message.message or ""
    processed_text = process_text_content(
        raw_text, 
        source_username=source_username, 
        dest_username=dest_username
    )

    reply_to_id = None
    if message.reply_to and message.reply_to.reply_to_msg_id:
        old_reply_id = message.reply_to.reply_to_msg_id
        reply_to_id = reply_mapping.get(old_reply_id)

    try:
        sent_msg = None

        if media_type in ["photo", "video", "voice", "audio", "gif", "sticker", "document", "round_video"]:
            sent_msg = await send_file_safe(
                client, destination_id, message.media,
                caption=processed_text, reply_to=reply_to_id
            )
        elif media_type == "poll" and hasattr(message.media, "poll"):
            sent_msg = await send_message_safe(
                client, destination_id, file=message.media.poll, reply_to=reply_to_id
            )
        elif media_type == "dice":
            sent_msg = await send_message_safe(
                client, destination_id, file=message.media, reply_to=reply_to_id
            )
        elif media_type in ["location", "contact"]:
            sent_msg = await send_message_safe(
                client, destination_id, message=message.media, reply_to=reply_to_id
            )
        else:
            if processed_text or message.entities:
                entities_to_pass = message.entities if (processed_text == raw_text) else None
                sent_msg = await send_message_safe(
                    client, destination_id, message=processed_text,
                    formatting_entities=entities_to_pass, reply_to=reply_to_id,
                    link_preview=True
                )

        if sent_msg:
            first_msg_id = sent_msg[0].id if isinstance(sent_msg, list) else sent_msg.id
            reply_mapping[message.id] = first_msg_id

            if getattr(message, 'pinned', False) and config.SYNC_PINNED_MESSAGES:
                await pin_message_safe(client, destination_id, first_msg_id)

            return True

        return False

    except Exception as e:
        logger.error(f"Failed processing message ID {message.id}: {e}")
        raise e
