from typing import Tuple
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, MessageMediaGeo,
    MessageMediaContact, DocumentAttributeAudio, DocumentAttributeVideo,
    DocumentAttributeSticker, DocumentAttributeAnimated,
    MessageMediaWebPage, MessageMediaPoll, MessageMediaDice,
    MessageMediaVenue, MessageMediaGeoLive
)

def is_album_element(message) -> bool:
    return getattr(message, 'grouped_id', None) is not None

def determine_media_attributes(media) -> Tuple[str, int]:
    if not media:
        return "text", 0

    if isinstance(media, MessageMediaWebPage):
        return "webpage", 0

    if isinstance(media, MessageMediaPhoto):
        return "photo", 0

    if isinstance(media, MessageMediaPoll):
        return "poll", 0

    if isinstance(media, MessageMediaDice):
        return "dice", 0

    if isinstance(media, (MessageMediaGeo, MessageMediaVenue, MessageMediaGeoLive)):
        return "location", 0

    if isinstance(media, MessageMediaContact):
        return "contact", 0

    if isinstance(media, MessageMediaDocument) and media.document:
        file_size = getattr(media.document, 'size', 0)
        for attr in getattr(media.document, 'attributes', []):
            if isinstance(attr, DocumentAttributeSticker):
                return "sticker", file_size
            elif isinstance(attr, DocumentAttributeAnimated):
                return "gif", file_size
            elif isinstance(attr, DocumentAttributeVideo):
                if getattr(attr, 'round_message', False):
                    return "round_video", file_size
                else:
                    return "video", file_size
            elif isinstance(attr, DocumentAttributeAudio):
                if getattr(attr, 'voice', False):
                    return "voice", file_size
                else:
                    return "audio", file_size
        return "document", file_size

    return "unknown", 0
