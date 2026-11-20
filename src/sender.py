import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import config
from src.utils import apply_delay, truncate_caption
from src.logger import get_logger

logger = get_logger()

async def send_message_safe(client: TelegramClient, entity, **kwargs) -> any:
    if config.DESTINATION_TOPIC_ID and ('reply_to' not in kwargs or kwargs.get('reply_to') is None):
        kwargs['reply_to'] = config.DESTINATION_TOPIC_ID

    retries = 0
    while retries <= config.MAX_RETRIES:
        try:
            sent_msg = await client.send_message(entity, **kwargs)
            await apply_delay()
            return sent_msg
        except FloodWaitError as e:
            logger.warning(f"FloodWait encountered: sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            continue
        except Exception as e:
            retries += 1
            logger.error(f"Message send error (attempt {retries}/{config.MAX_RETRIES}): {e}")
            if retries > config.MAX_RETRIES:
                raise e
            await asyncio.sleep(1.0)

async def send_file_safe(client: TelegramClient, entity, file, **kwargs) -> any:
    if config.DESTINATION_TOPIC_ID and ('reply_to' not in kwargs or kwargs.get('reply_to') is None):
        kwargs['reply_to'] = config.DESTINATION_TOPIC_ID

    overflow_text = None
    caption = kwargs.get("caption")
    if caption and len(caption) > config.MAX_CAPTION_LENGTH:
        trimmed_caption, overflow_text = truncate_caption(caption, config.MAX_CAPTION_LENGTH)
        kwargs["caption"] = trimmed_caption

    retries = 0
    while retries <= config.MAX_RETRIES:
        try:
            sent_msg = await client.send_file(entity, file, **kwargs)
            await apply_delay()

            if overflow_text and config.SPLIT_LONG_CAPTION and sent_msg:
                first_msg_id = sent_msg[0].id if isinstance(sent_msg, list) else sent_msg.id
                try:
                    await client.send_message(entity, message=overflow_text, reply_to=first_msg_id)
                    await apply_delay()
                except Exception as ex:
                    logger.warning(f"Failed sending caption overflow text: {ex}")

            return sent_msg
        except FloodWaitError as e:
            logger.warning(f"FloodWait encountered during file send: sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
            continue
        except Exception as e:
            retries += 1
            logger.error(f"File send error (attempt {retries}/{config.MAX_RETRIES}): {e}")
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
