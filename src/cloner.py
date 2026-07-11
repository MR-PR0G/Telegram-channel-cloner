# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import asyncio
import time
from typing import List, Dict
from telethon import TelegramClient
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

import config
from src.progress import CloneProgress, save_progress, log_failed_message
from src.message_handler import process_single_message
from src.utils import format_timedelta, process_text_content, is_date_in_range
from src.logger import get_logger
from src.media import is_album_element
from src.sender import send_file_safe, pin_message_safe

logger = get_logger()
console = Console()

def generate_progress_table(
    source_title: str, dest_title: str, current_id: int, 
    copied: int, total: int, rate: float, elapsed: float, eta: float, status_text: str = "Active Running"
) -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right")
    table.add_column(style="white", justify="left")

    pct = (copied / total * 100) if total > 0 else 0.0

    table.add_row("Source:", source_title)
    table.add_row("Destination:", dest_title)
    table.add_row("Current Message ID:", str(current_id))
    table.add_row("Copied Status:", f"{copied} / {total} ({pct:.2f}%)")
    table.add_row("Transmission Speed:", f"{rate:.1f} msg/sec")
    table.add_row("Elapsed Time:", format_timedelta(elapsed))
    table.add_row("Estimated Remaining:", format_timedelta(eta))
    
    if "Disrupted" in status_text or "Recovering" in status_text:
        table.add_row("Engine Status:", f"[bold red]{status_text}[/bold red]")
    else:
        table.add_row("Engine Status:", f"[bold green]{status_text}[/bold green]")
        
    return table

async def execute_cloning(
    client: TelegramClient, source_id: int, destination_id: int, 
    source_title: str, destination_title: str, 
    source_username: str = "", dest_username: str = "",
    resume_from_msg_id: int = 0, initial_copied: int = 0
) -> None:
    
    logger.info(f"Resolving total channel message count for source ID: {source_id}")
    console.print("[yellow]Calculating remote history size... Please wait.[/yellow]")
    
    total_messages_count = 0
    while True:
        try:
            iter_kwargs = {}
            if config.SOURCE_TOPIC_ID:
                iter_kwargs['reply_to'] = config.SOURCE_TOPIC_ID

            async for _ in client.iter_messages(source_id, **iter_kwargs):
                total_messages_count += 1
            break
        except Exception as e:
            logger.warning(f"Network error while counting messages: {e}. Retrying...")
            try:
                await client.disconnect()
            except Exception:
                pass
            await asyncio.sleep(2.0)
            try:
                await client.connect()
            except Exception:
                pass
        
    logger.info(f"Target contains {total_messages_count} messages.")

    reply_map_registry: Dict[int, int] = {}
    copied_tracker = initial_copied
    start_time = time.time()

    album_accumulator: List[any] = []
    current_album_id = None
    current_checkpoint_id = resume_from_msg_id

    async def flush_album_buffer() -> None:
        nonlocal copied_tracker
        if not album_accumulator:
            return
        
        caption_text = ""
        reply_to_id = None
        has_pinned_item = False

        media_payload = []
        for msg in album_accumulator:
            if not is_date_in_range(msg.date):
                continue

            if getattr(msg, 'pinned', False):
                has_pinned_item = True

            if msg.message:
                caption_text = process_text_content(
                    msg.message, 
                    source_username=source_username, 
                    dest_username=dest_username
                ) or ""

            if msg.reply_to and not reply_to_id:
                old_reply_to_msg_id = msg.reply_to.reply_to_msg_id
                reply_to_id = reply_map_registry.get(old_reply_to_msg_id)

            if msg.media:
                media_payload.append(msg.media)

        if not media_payload:
            album_accumulator.clear()
            return

        try:
            sent_group = await send_file_safe(
                client, destination_id, media_payload, 
                caption=caption_text, reply_to=reply_to_id
            )
            if sent_group:
                for idx, original_msg in enumerate(album_accumulator):
                    try:
                        reply_map_registry[original_msg.id] = sent_group[idx].id
                    except IndexError:
                        reply_map_registry[original_msg.id] = sent_group[0].id
                    copied_tracker += 1

                if has_pinned_item and config.SYNC_PINNED_MESSAGES:
                    await pin_message_safe(client, destination_id, sent_group[0].id)

                last_processed_id = album_accumulator[-1].id
                save_progress(CloneProgress(
                    source_id=source_id, destination_id=destination_id,
                    last_source_msg_id=last_processed_id, copied_count=copied_tracker,
                    timestamp=time.time(), source_title=source_title, destination_title=destination_title
                ))
        except Exception as exc:
            logger.error(f"Failed replicating media group structures: {exc}")
            for original_msg in album_accumulator:
                log_failed_message(original_msg.id)
        finally:
            album_accumulator.clear()

    grid_layout = Layout()
    status_msg = "Active Running"
    grid_layout.update(Panel(generate_progress_table(
        source_title, destination_title, current_checkpoint_id, 
        copied_tracker, total_messages_count, 0.0, 0.0, 0.0, status_msg
    ), title="Telegram Channel Clone Theta Engine", border_style="green"))

    CHUNK_SIZE = 30

    with Live(grid_layout, refresh_per_second=4) as live_display:
        while True:
            messages_chunk = None
            
            try:
                async def fetch_chunk():
                    get_kwargs = {
                        "limit": CHUNK_SIZE,
                        "offset_id": current_checkpoint_id,
                        "reverse": True
                    }
                    if config.SOURCE_TOPIC_ID:
                        get_kwargs["reply_to"] = config.SOURCE_TOPIC_ID

                    return await client.get_messages(source_id, **get_kwargs)

                messages_chunk = await asyncio.wait_for(fetch_chunk(), timeout=8.0)
                status_msg = "Active Running"
                
            except (asyncio.TimeoutError, Exception) as net_err:
                logger.error(f"Network connection failure or frozen socket at ID {current_checkpoint_id}: {net_err}")
                
                retry_seconds = 0
                while True:
                    retry_seconds += 2
                    status_msg = f"Network Disrupted! Recovering connection session (Paused {retry_seconds}s)..."
                    
                    grid_layout.update(Panel(generate_progress_table(
                        source_title, destination_title, current_checkpoint_id,
                        copied_tracker, total_messages_count, 0.0, time.time() - start_time, 0.0, status_msg
                    ), title="Telegram Channel Clone Theta Engine", border_style="red"))
                    
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                        
                    await asyncio.sleep(2.0)
                    
                    try:
                        await client.connect()
                        await client.get_me()
                        break
                    except Exception:
                        pass
                continue

            if not messages_chunk:
                break

            for raw_message in messages_chunk:
                current_checkpoint_id = raw_message.id

                if is_album_element(raw_message):
                    if current_album_id is not None and raw_message.grouped_id != current_album_id:
                        await flush_album_buffer()
                    current_album_id = raw_message.grouped_id
                    album_accumulator.append(raw_message)
                    continue
                else:
                    if album_accumulator:
                        await flush_album_buffer()
                        current_album_id = None

                try:
                    cloned_successfully = await process_single_message(
                        client, raw_message, destination_id, reply_map_registry,
                        source_username=source_username, dest_username=dest_username
                    )
                    if cloned_successfully:
                        copied_tracker += 1
                except Exception:
                    log_failed_message(current_checkpoint_id)

                current_elapsed = time.time() - start_time
                current_rate = (copied_tracker - initial_copied) / current_elapsed if current_elapsed > 0 else 0.0
                
                remaining_messages = max(0, total_messages_count - copied_tracker)
                computed_eta = (remaining_messages / current_rate) if current_rate > 0 else 0.0

                save_progress(CloneProgress(
                    source_id=source_id, destination_id=destination_id,
                    last_source_msg_id=current_checkpoint_id, copied_count=copied_tracker,
                    timestamp=time.time(), source_title=source_title, destination_title=destination_title
                ))

                grid_layout.update(Panel(generate_progress_table(
                    source_title, destination_title, current_checkpoint_id,
                    copied_tracker, total_messages_count, current_rate, current_elapsed, computed_eta, status_msg
                ), title="Telegram Channel Clone Theta Engine", border_style="green"))

            if album_accumulator:
                await flush_album_buffer()

    if album_accumulator:
        await flush_album_buffer()

    logger.info("Channel cloning process finished successfully.")