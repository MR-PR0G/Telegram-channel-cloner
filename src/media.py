# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

from typing import Tuple
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, MessageMediaGeo,
    MessageMediaContact, DocumentAttributeAudio, DocumentAttributeVideo,
    DocumentAttributeSticker, DocumentAttributeAnimated
)

def is_album_element(message) -> bool:
    return message.grouped_id is not None

def determine_media_attributes(media) -> Tuple[str, int]:
    if not media:
        return "text", 0

    file_size = 0

    if isinstance(media, MessageMediaPhoto):
        return "photo", 0

    elif isinstance(media, MessageMediaDocument) and media.document:
        file_size = getattr(media.document, 'size', 0)
        for attr in media.document.attributes:
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

    elif isinstance(media, MessageMediaGeo):
        return "location", 0

    elif isinstance(media, MessageMediaContact):
        return "contact", 0

    return "unknown", 0