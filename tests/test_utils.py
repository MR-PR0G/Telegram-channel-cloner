from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import config
from src.utils import (
    format_timedelta, truncate_caption, process_text_content,
    is_date_in_range, is_media_allowed, get_entity_display_name, get_entity_username
)

def test_format_timedelta():
    assert format_timedelta(0) == "00:00:00"
    assert format_timedelta(65) == "00:01:05"
    assert format_timedelta(3665) == "01:01:05"

def test_truncate_caption_within_limit():
    text = "Short caption"
    head, tail = truncate_caption(text, max_length=100)
    assert head == text
    assert tail is None

def test_truncate_caption_exceeding_limit():
    long_text = ("Line 1 paragraph.\n" * 40) + ("Word " * 100)
    assert len(long_text) > 1024
    head, tail = truncate_caption(long_text, max_length=1024)
    assert len(head) <= 1024
    assert tail is not None
    assert len(head) + len(tail) == len(long_text.strip()) or len(head) > 500

def test_process_text_content_replacement():
    with patch.object(config, "ENABLE_TEXT_REPLACEMENT", True), \
         patch.object(config, "AUTO_REPLACE_USERNAMES", True), \
         patch.object(config, "REPLACE_DICTIONARY", {"bad": "good"}), \
         patch.object(config, "CUSTOM_HEADER", "HEADER"), \
         patch.object(config, "CUSTOM_FOOTER", "FOOTER"):

        raw = "Contact @oldsource for bad deals."
        processed = process_text_content(raw, source_username="oldsource", dest_username="newtarget")
        assert "@newtarget" in processed
        assert "good deals" in processed
        assert processed.startswith("HEADER\n\n")
        assert processed.endswith("\n\nFOOTER")

def test_is_date_in_range():
    with patch.object(config, "START_DATE", "2026-01-01"), \
         patch.object(config, "END_DATE", "2026-01-10"):

        dt_before = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)
        dt_during = datetime(2026, 1, 10, 15, 30, tzinfo=timezone.utc)
        dt_after = datetime(2026, 1, 11, 0, 1, tzinfo=timezone.utc)

        assert not is_date_in_range(dt_before)
        assert is_date_in_range(dt_during)
        assert not is_date_in_range(dt_after)

def test_is_media_allowed():
    with patch.object(config, "ALLOWED_MEDIA_TYPES", ["photo", "video"]), \
         patch.object(config, "MAX_FILE_SIZE_MB", 10.0):

        assert is_media_allowed("photo", 5 * 1024 * 1024)
        assert not is_media_allowed("audio", 5 * 1024 * 1024)
        assert not is_media_allowed("photo", 15 * 1024 * 1024)

def test_get_entity_display_name():
    # Saved messages
    mock_self = MagicMock()
    mock_self.is_self = True
    assert get_entity_display_name(mock_self) == "Saved Messages"

    # Channel / Chat with title
    mock_channel = MagicMock(spec=["title"])
    mock_channel.title = "Announcements"
    assert get_entity_display_name(mock_channel) == "Announcements"

    # User with first & last name
    mock_user = MagicMock(spec=["first_name", "last_name"])
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    assert get_entity_display_name(mock_user) == "John Doe"

    # User with username only
    mock_username_only = MagicMock(spec=["username"])
    mock_username_only.username = "johndoe"
    assert get_entity_display_name(mock_username_only) == "@johndoe"
