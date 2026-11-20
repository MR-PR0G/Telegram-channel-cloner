import os
import tempfile
import pytest
from unittest.mock import patch
import config
from src.progress import (
    CloneProgress, save_progress, load_progress, clear_progress,
    log_failed_message, load_failed_messages, remove_failed_message,
    remove_failed_messages, get_failed_messages_count, clear_failed_messages
)

@pytest.fixture(autouse=True)
def isolated_files(tmp_path):
    prog_file = str(tmp_path / "progress.json")
    failed_file = str(tmp_path / "failed_messages.json")
    with patch.object(config, "PROGRESS_FILE", prog_file), patch.object(config, "FAILED_LOG_FILE", failed_file):
        yield

def test_save_and_load_progress():
    progress = CloneProgress(
        source_id=-1001234567,
        destination_id=-1009876543,
        last_source_msg_id=150,
        copied_count=45,
        timestamp=1700000000.0,
        source_title="Source Channel",
        destination_title="Target Channel"
    )
    save_progress(progress)
    loaded = load_progress()
    assert loaded is not None
    assert loaded.source_id == -1001234567
    assert loaded.last_source_msg_id == 150
    assert loaded.copied_count == 45
    assert loaded.source_title == "Source Channel"

    clear_progress()
    assert load_progress() is None

def test_failed_messages_lifecycle():
    assert get_failed_messages_count() == 0
    assert load_failed_messages() == []

    log_failed_message(101)
    log_failed_message(102)
    log_failed_message(101)  # duplicate check

    assert load_failed_messages() == [101, 102]
    assert get_failed_messages_count() == 2

    remove_failed_message(101)
    assert load_failed_messages() == [102]

    log_failed_message(105)
    log_failed_message(108)
    remove_failed_messages([102, 108])
    assert load_failed_messages() == [105]

    clear_failed_messages()
    assert load_failed_messages() == []
