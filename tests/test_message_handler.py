import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telethon.tl.types import MessageService, MessageMediaPhoto
import config
from src.message_handler import process_single_message

@pytest.mark.asyncio
async def test_process_single_message_service_skipped():
    client = MagicMock()
    service_msg = MagicMock(spec=MessageService)
    res = await process_single_message(client, service_msg, destination_id=123, reply_mapping={})
    assert res is False

@pytest.mark.asyncio
async def test_process_single_message_min_max_id_filter():
    client = MagicMock()
    msg = MagicMock()
    msg.id = 50
    msg.media = None
    msg.message = "Test"
    msg.reply_to = None
    msg.date = None
    msg.entities = None

    with patch.object(config, "MIN_MSG_ID", 100):
        res = await process_single_message(client, msg, destination_id=123, reply_mapping={})
        assert res is False

    with patch.object(config, "MIN_MSG_ID", 0), patch.object(config, "MAX_MSG_ID", 40):
        res = await process_single_message(client, msg, destination_id=123, reply_mapping={})
        assert res is False

@pytest.mark.asyncio
async def test_process_single_message_text_success():
    client = MagicMock()
    sent_mock = MagicMock()
    sent_mock.id = 999
    client.send_message = AsyncMock(return_value=sent_mock)

    msg = MagicMock()
    msg.id = 15
    msg.media = None
    msg.message = "Hello world"
    msg.reply_to = None
    msg.date = None
    msg.entities = None
    msg.pinned = False

    reply_map = {}
    with patch("src.sender.apply_delay", AsyncMock()):
        success = await process_single_message(client, msg, destination_id=123, reply_mapping=reply_map)
        assert success is True
        assert reply_map[15] == 999
