# Telegram Channel Cloner

A resilient, asynchronous CLI tool built with Python and Telethon to copy message history from any accessible Telegram channel, group, or Saved Messages to a destination chat.

Designed for large channel migrations where network interruptions, Telegram rate limits, and broken sockets often cause standard scripts to fail.

---

## Features

- **Sequential Replication**: Clones messages in chronological order (oldest to newest).
- **Auto-Retry Engine**: Re-attempts skipped or failed messages directly from `failed_messages.json` (`--retry-failed`) without re-cloning previous messages.
- **Caption Truncation & Overflow Chaining**: Safely cuts media captions at Telegram's 1024-character limit and sends remaining text as a chained reply.
- **Batch Cooldown**: Configurable sleep periods between batches (e.g. 60s pause every 100 messages) to avoid sliding-window `FLOOD_WAIT` restrictions.
- **Fast Remote Sizing**: Resolves total channel message count in a single API call instead of scanning the full history.
- **Connection Recovery**: Automatic socket reconnect and state preservation on IP or proxy drops.
- **Media & Album Support**: Handles single media, documents, voice, stickers, and grouped media albums across chunks without fragmentation.
- **Filtering**: Filter by allowed media types, max file size in MB, date range, or message ID boundaries.
- **Text & Branding Cleanup**: Optional regex cleanup, username handle replacement, and custom signatures.
- **Proxy Support**: Works with HTTP, SOCKS5, and SOCKS4 proxies.
- **Interactive UI**: Clean Rich terminal dashboard showing real-time speed, progress percentage, and ETA.

---

## Installation

### Requirements
- Python 3.12+
- Telegram `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)

```bash
git clone https://github.com/MR-PR0G/Telegram-channel-cloner.git
cd Telegram-channel-cloner

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Usage

### Interactive Mode
Launch the wizard to search and select source and destination channels:
```bash
python main.py
```

### Command-Line Options

| Flag | Argument | Description |
|---|---|---|
| `--retry-failed` | - | Process failed messages from `failed_messages.json` |
| `--resume` | - | Auto-resume previous session without confirmation |
| `--no-resume` | - | Start new session, discarding previous progress |
| `--batch-size` | `int` | Message count per batch before cooldown pause |
| `--batch-cooldown` | `float` | Pause duration in seconds after each batch |
| `--min-id` | `int` | Start cloning from this minimum message ID |
| `--max-id` | `int` | Stop cloning at this maximum message ID |

#### Examples
Retry failed messages from a previous run:
```bash
python main.py --retry-failed
```

Clone with a 60-second cooldown every 100 messages:
```bash
python main.py --batch-size 100 --batch-cooldown 60
```

Resume interrupted session:
```bash
python main.py --resume
```

---

## Configuration

Settings can be managed in `config.py` or via environment variables (`.env`):

```python
# Credentials
API_ID = 0
API_HASH = ""

# Proxy (HTTP, SOCKS5, SOCKS4)
USE_PROXY = False
PROXY_TYPE = "HTTP"
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 2080

# Delays & Human Behavior
ENABLE_RANDOM_DELAY = True
MIN_DELAY = 0.3
MAX_DELAY = 1.0

# Rate-Limit Shield
BATCH_SIZE = 100
BATCH_COOLDOWN_SECONDS = 0.0  # Set > 0 to enable batch resting

# Caption Handling
MAX_CAPTION_LENGTH = 1024
SPLIT_LONG_CAPTION = True  # Send text overflow as reply
```

---

## Development & Tests

Run test suite:
```bash
pip install -r requirements-dev.txt
pytest tests/
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
