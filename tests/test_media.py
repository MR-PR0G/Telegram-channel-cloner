from unittest.mock import MagicMock
from telethon.tl.types import (
    MessageMediaWebPage, MessageMediaPhoto, MessageMediaPoll,
    MessageMediaDice, MessageMediaContact, MessageMediaGeo
)
from src.media import determine_media_attributes, is_album_element

def test_is_album_element():
    msg_single = MagicMock()
    msg_single.grouped_id = None
    assert is_album_element(msg_single) is False

    msg_album = MagicMock()
    msg_album.grouped_id = 987654321
    assert is_album_element(msg_album) is True

def test_determine_media_attributes_types():
    assert determine_media_attributes(None) == ("text", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaWebPage)) == ("webpage", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaPhoto)) == ("photo", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaPoll)) == ("poll", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaDice)) == ("dice", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaContact)) == ("contact", 0)
    assert determine_media_attributes(MagicMock(spec=MessageMediaGeo)) == ("location", 0)
