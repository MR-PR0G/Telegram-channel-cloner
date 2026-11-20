# 🚀 Telegram Channel Clone (v0.1.0)

An ultra-resilient, production-grade asynchronous CLI application built with **Python 3.12+** and **Telethon** to seamlessly clone message histories from any accessible Telegram channel, group, or **Saved Messages** to a destination channel/group.

## ⚡ Quick Overview

Cloning massive Telegram channels (10,000+ to 50,000+ messages) often fails due to proxy disconnects, IP changes, rate limits, and frozen sockets. **Telegram Channel Cloner** is engineered to handle unstable networks with **zero freezing**, **smart chunked pagination**, **auto-reconnection**, **resumable progress tracking**, and an **auto-retry engine for failed messages**.

<p align="center">
  <img src="Demos/1.png" alt="Header Banner" width="100%" style="max-width: 100%; height: auto;" />
</p>

<p align="center">
  <img src="Demos/2.png" alt="Dashboard Preview" width="100%" style="max-width: 100%; height: auto;" />
</p>

## 🌟 Key Features

- 🔄 **100% Chronological Execution**: Copies messages strictly from oldest to newest, preserving historical sequence perfectly.
- 🔁 **Failed Messages Auto-Retry Engine**: Retry failed messages saved in `failed_messages.json` with `--retry-failed` without re-cloning already copied messages or resetting progress.
- ✂️ **Smart Caption Truncation & Chaining**: Conforms to Telegram's 1024-character caption limits on media. Automatically splits overflow text into chained reply messages to prevent `Caption too long` exceptions.
- ☕ **Batch Pause & Account Cooldown**: Built-in resting periods (e.g., pause 60s every 100 messages) to shield accounts against Telegram's sliding-window hourly/daily `FLOOD_WAIT` rate limits.
- ⚡ **Instant Remote Size Calculation**: Fast single-roundtrip message count resolution without exhausting quotas.
- 🛡️ **Zero-Freezing Network Resilience**: Socket recovery mechanism that auto-reconnects on IP changes or proxy drops.
- 🌐 **Multi-Proxy Support**: Supports HTTP, SOCKS5, and SOCKS4 proxies via `python-socks`.
- 💬 **Saved Messages Integration**: Clone directly to or from your personal "Saved Messages" using simple keywords (`saved`).
- 🔍 **Single-Pass Fast Search**: Caches all accessible dialogs once with a live scanning progress bar for instant searching.
- ✏️ **Text Cleaning, Auto Replacement & Signatures**: Auto-replace channel handles, remove custom text/patterns, and inject custom headers or footers.
- 📂 **Full Media & Album Compatibility**: Handles Text, Photos, Videos, Media Groups (Albums), Voice, GIFs, Documents, Stickers, Locations, Contacts, and Round Videos without album-splitting bugs across chunk boundaries.
- 🎛️ **Advanced Filtering Options**: Restrict cloning by allowed media types, max file size limits (e.g., max 50MB), Date Ranges (`YYYY-MM-DD`), or Message ID boundaries.
- 📌 **Pinned Messages & Forum Topics**: Syncs pinned messages automatically and supports Telegram Supergroup Forum Topics (Threads).
- ⏳ **Human Delay Jitter**: Configurable random delay between messages for natural behavior under Telegram's rate limits.
- 📊 **Live Rich CLI Dashboard**: Real-time terminal UI displaying copy speed, estimated time remaining (ETA), message count, and status alerts.
- 💾 **Resumable Progress**: Saves state after every successfully copied message and resumes anytime from where you left off.
- 🧪 **Automated Testing Suite**: Full unit and integration test coverage using `pytest`.

---

## 💻 Installation & Setup Guide

### 📋 Prerequisites

- **Python**: Version `3.12` or higher.
- **Git**: Installed on your system.
- **Telegram Account**: Access to your account to obtain API credentials.

---

### 🔑 Step 1: Obtain Telegram API Credentials

1. Log in to your account at [my.telegram.org](https://my.telegram.org).
2. Go to **API development tools**.
3. Create a new application.
4. Copy your unique **`api_id`** and **`api_hash`**.

---

### 🐧 Step 2: Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/MR-PR0G/Telegram-channel-cloner.git
cd Telegram-channel-cloner
```

#### 2. Create & Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage & CLI Commands

### 1. Interactive Mode
Run the application interactively:
```bash
python main.py
```
If a previous session or failed messages exist, the tool will prompt you automatically.

### 2. Retry Failed Messages Only
To retry only the failed messages stored in `failed_messages.json` without modifying your `progress.json` or re-sending already copied messages:
```bash
python main.py --retry-failed
```

### 3. Automatic Session Resuming
To resume immediately from the last recorded message without confirmation:
```bash
python main.py --resume
```

### 4. Batch Cooldown (For Massive Channels)
To copy in batches of 100 messages and rest for 60 seconds between batches:
```bash
python main.py --batch-size 100 --batch-cooldown 60
```

### 5. CLI Arguments Reference

| Argument | Type | Description |
|---|---|---|
| `--retry-failed` | flag | Re-attempt copying all messages logged in `failed_messages.json` |
| `--resume` | flag | Auto-resume previous cloning session without prompt |
| `--no-resume` | flag | Start a fresh cloning session without resuming |
| `--batch-size <N>` | int | Number of messages to copy before triggering cooldown |
| `--batch-cooldown <SEC>` | float | Seconds to pause during batch cooldown |
| `--min-id <ID>` | int | Filter: lowest message ID to process |
| `--max-id <ID>` | int | Filter: highest message ID to process |

---

## 🛠️ Configuration (`config.py`)

Settings can be defined directly in `config.py` or via environment variables (`.env`):

```python
# API credentials (or set TELEGRAM_API_ID / TELEGRAM_API_HASH env vars)
API_ID = 24292412
API_HASH = "..."

# Proxy Configuration
USE_PROXY = True
PROXY_TYPE = "HTTP"       # HTTP, SOCKS5, or SOCKS4
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 2080

# Delays & Human Jitter
ENABLE_RANDOM_DELAY = True
MIN_DELAY = 0.3
MAX_DELAY = 1.0

# Batch Pause / Rate-Limit Protection
BATCH_SIZE = 100
BATCH_COOLDOWN_SECONDS = 0.0   # Set e.g. 60.0 to rest 1 minute every 100 messages

# Caption Safety
MAX_CAPTION_LENGTH = 1024
SPLIT_LONG_CAPTION = True      # Send remaining caption as chained reply
```

---

## 🧪 Running Tests

To run the automated test suite:
```bash
pytest tests/
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
