import asyncio
import time
from typing import List, Dict, Optional
from telethon import TelegramClient
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

import config
from src.progress import (
    CloneProgress, save_progress, log_failed_message,
    load_failed_messages, remove_failed_message, remove_failed_messages
)
from src.message_handler import process_single_message
from src.utils import format_timedelta, process_text_content, is_date_in_range
from src.logger import get_logger
from src.media import is_album_element
from src.sender import send_file_safe, pin_message_safe

logger = get_logger()
console = Console()

def generate_progress_table(
    source_title: str, dest_title: str, current_id: int, 
    copied: int, total: int, rate: float, elapsed: float, eta: float, status_text: str = "Running"
) -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", justify="right")
    table.add_column(style="white", justify="left")

    pct = (copied / total * 100) if total > 0 else 0.0

    table.add_row("Source:", source_title)
    table.add_row("Destination:", dest_title)
    table.add_row("Message ID:", str(current_id))
    table.add_row("Progress:", f"{copied} / {total} ({pct:.1f}%)")
    table.add_row("Speed:", f"{rate:.1f} msg/s")
    table.add_row("Elapsed:", format_timedelta(elapsed))
    table.add_row("ETA:", format_timedelta(eta))

    if "Error" in status_text or "Disrupted" in status_text:
        table.add_row("Status:", f"[bold red]{status_text}[/bold red]")
    elif "Cooldown" in status_text:
        table.add_row("Status:", f"[bold yellow]{status_text}[/bold yellow]")
    else:
        table.add_row("Status:", f"[bold green]{status_text}[/bold green]")

    return table

async def get_total_messages_count(client: TelegramClient, source_id: int) -> int:
    try:
        kwargs = {}
        if config.SOURCE_TOPIC_ID:
            kwargs['reply_to'] = config.SOURCE_TOPIC_ID
        res = await client.get_messages(source_id, limit=0, **kwargs)
        if res and hasattr(res, 'total') and res.total is not None:
            return res.total
    except Exception as e:
        logger.warning(f"Fast total calculation failed: {e}. Falling back to iteration.")

    count = 0
    try:
        iter_kwargs = {}
        if config.SOURCE_TOPIC_ID:
            iter_kwargs['reply_to'] = config.SOURCE_TOPIC_ID
        async for _ in client.iter_messages(source_id, **iter_kwargs):
            count += 1
    except Exception as ex:
        logger.error(f"Iterative counting error: {ex}")
    return count

async def execute_cloning(
    client: TelegramClient, source_id: int, destination_id: int, 
    source_title: str, destination_title: str, 
    source_username: str = "", dest_username: str = "",
    resume_from_msg_id: int = 0, initial_copied: int = 0
) -> None:
    logger.info(f"Starting cloning from {source_title} ({source_id}) to {destination_title} ({destination_id})")

    total_messages_count = await get_total_messages_count(client, source_id)
    logger.info(f"Total source messages: {total_messages_count}")

    reply_map_registry: Dict[int, int] = {}
    copied_tracker = initial_copied
    batch_counter = 0
    start_time = time.time()

    album_accumulator: List[any] = []
    current_album_id = None
    current_checkpoint_id = resume_from_msg_id

    async def flush_album_buffer() -> None:
        nonlocal copied_tracker, batch_counter
        if not album_accumulator:
            return

        caption_text = ""
        reply_to_id = None
        has_pinned = False
        media_payload = []

        for msg in album_accumulator:
            if not is_date_in_range(msg.date):
                continue
            if getattr(msg, 'pinned', False):
                has_pinned = True
            if msg.message:
                caption_text = process_text_content(
                    msg.message, source_username=source_username, dest_username=dest_username
                ) or ""
            if msg.reply_to and not reply_to_id:
                reply_to_id = reply_map_registry.get(msg.reply_to.reply_to_msg_id)
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
                sent_items = sent_group if isinstance(sent_group, list) else [sent_group]
                for idx, orig_msg in enumerate(album_accumulator):
                    mapped_msg = sent_items[idx] if idx < len(sent_items) else sent_items[0]
                    reply_map_registry[orig_msg.id] = mapped_msg.id
                    copied_tracker += 1
                    batch_counter += 1

                if has_pinned and config.SYNC_PINNED_MESSAGES:
                    await pin_message_safe(client, destination_id, sent_items[0].id)

                last_id = album_accumulator[-1].id
                save_progress(CloneProgress(
                    source_id=source_id, destination_id=destination_id,
                    last_source_msg_id=last_id, copied_count=copied_tracker,
                    timestamp=time.time(), source_title=source_title, destination_title=destination_title
                ))
        except Exception as exc:
            logger.error(f"Failed sending media group: {exc}")
            for orig_msg in album_accumulator:
                log_failed_message(orig_msg.id)
        finally:
            album_accumulator.clear()

    grid_layout = Layout()
    status_msg = "Running"
    grid_layout.update(Panel(generate_progress_table(
        source_title, destination_title, current_checkpoint_id,
        copied_tracker, total_messages_count, 0.0, 0.0, 0.0, status_msg
    ), title="Telegram Channel Cloner", border_style="cyan"))

    CHUNK_SIZE = 50

    with Live(grid_layout, refresh_per_second=4):
        while True:
            # Batch cooldown pause check
            if config.BATCH_SIZE > 0 and config.BATCH_COOLDOWN_SECONDS > 0 and batch_counter >= config.BATCH_SIZE:
                cooldown_remaining = config.BATCH_COOLDOWN_SECONDS
                while cooldown_remaining > 0:
                    status_msg = f"Cooldown: resting for {cooldown_remaining:.0f}s..."
                    elapsed = time.time() - start_time
                    grid_layout.update(Panel(generate_progress_table(
                        source_title, destination_title, current_checkpoint_id,
                        copied_tracker, total_messages_count, 0.0, elapsed, 0.0, status_msg
                    ), title="Telegram Channel Cloner", border_style="yellow"))
                    sleep_step = min(1.0, cooldown_remaining)
                    await asyncio.sleep(sleep_step)
                    cooldown_remaining -= sleep_step
                batch_counter = 0
                status_msg = "Running"

            try:
                get_kwargs = {
                    "limit": CHUNK_SIZE,
                    "offset_id": current_checkpoint_id,
                    "reverse": True
                }
                if config.SOURCE_TOPIC_ID:
                    get_kwargs["reply_to"] = config.SOURCE_TOPIC_ID

                messages_chunk = await asyncio.wait_for(client.get_messages(source_id, **get_kwargs), timeout=12.0)
                status_msg = "Running"
            except (asyncio.TimeoutError, Exception) as net_err:
                logger.error(f"Network error at message ID {current_checkpoint_id}: {net_err}")
                status_msg = "Connection Disrupted. Reconnecting..."
                grid_layout.update(Panel(generate_progress_table(
                    source_title, destination_title, current_checkpoint_id,
                    copied_tracker, total_messages_count, 0.0, time.time() - start_time, 0.0, status_msg
                ), title="Telegram Channel Cloner", border_style="red"))
                await asyncio.sleep(3.0)
                try:
                    await client.connect()
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
                    success = await process_single_message(
                        client, raw_message, destination_id, reply_map_registry,
                        source_username=source_username, dest_username=dest_username
                    )
                    if success:
                        copied_tracker += 1
                        batch_counter += 1
                except Exception:
                    log_failed_message(current_checkpoint_id)

                elapsed = time.time() - start_time
                rate = (copied_tracker - initial_copied) / elapsed if elapsed > 0 else 0.0
                remaining = max(0, total_messages_count - copied_tracker)
                eta = (remaining / rate) if rate > 0 else 0.0

                save_progress(CloneProgress(
                    source_id=source_id, destination_id=destination_id,
                    last_source_msg_id=current_checkpoint_id, copied_count=copied_tracker,
                    timestamp=time.time(), source_title=source_title, destination_title=destination_title
                ))

                grid_layout.update(Panel(generate_progress_table(
                    source_title, destination_title, current_checkpoint_id,
                    copied_tracker, total_messages_count, rate, elapsed, eta, status_msg
                ), title="Telegram Channel Cloner", border_style="cyan"))

    if album_accumulator:
        await flush_album_buffer()

    logger.info("Channel cloning sequence completed.")

async def execute_retry_failed_messages(
    client: TelegramClient, source_id: int, destination_id: int,
    source_title: str, destination_title: str,
    source_username: str = "", dest_username: str = ""
) -> int:
    failed_ids = load_failed_messages()
    if not failed_ids:
        console.print("[green]No failed messages found to retry.[/green]")
        return 0

    total_failed = len(failed_ids)
    console.print(f"[bold cyan]Retrying {total_failed} failed message(s)...[/bold cyan]")
    logger.info(f"Retrying {total_failed} failed messages for {source_title} -> {destination_title}")

    reply_map: Dict[int, int] = {}
    recovered_count = 0
    start_time = time.time()

    grid_layout = Layout()
    status_msg = "Retrying Failed Messages"
    grid_layout.update(Panel(generate_progress_table(
        source_title, destination_title, 0,
        0, total_failed, 0.0, 0.0, 0.0, status_msg
    ), title="Retry Engine", border_style="magenta"))

    with Live(grid_layout, refresh_per_second=4):
        # Process in batches of IDs
        BATCH_FETCH_SIZE = 20
        for i in range(0, total_failed, BATCH_FETCH_SIZE):
            chunk_ids = failed_ids[i:i + BATCH_FETCH_SIZE]
            try:
                messages = await client.get_messages(source_id, ids=chunk_ids)
                if not messages:
                    continue
                if not isinstance(messages, list):
                    messages = [messages]

                for msg in messages:
                    if not msg:
                        continue
                    try:
                        success = await process_single_message(
                            client, msg, destination_id, reply_map,
                            source_username=source_username, dest_username=dest_username
                        )
                        if success:
                            recovered_count += 1
                            remove_failed_message(msg.id)
                    except Exception as e:
                        logger.error(f"Retry failed for message {msg.id}: {e}")

                    elapsed = time.time() - start_time
                    rate = recovered_count / elapsed if elapsed > 0 else 0.0
                    remaining = max(0, total_failed - recovered_count)
                    eta = (remaining / rate) if rate > 0 else 0.0

                    grid_layout.update(Panel(generate_progress_table(
                        source_title, destination_title, msg.id,
                        recovered_count, total_failed, rate, elapsed, eta, status_msg
                    ), title="Retry Engine", border_style="magenta"))

            except Exception as ex:
                logger.error(f"Error fetching batch during retry: {ex}")
                await asyncio.sleep(2.0)

    console.print(f"\n[bold green]Retry completed. Recovered: {recovered_count}/{total_failed}[/bold green]")
    remaining_count = len(load_failed_messages())
    if remaining_count == 0:
        console.print("[green]All failed messages successfully resolved and cleared.[/green]")
    else:
        console.print(f"[yellow]{remaining_count} messages remain unrecovered in failed_messages.json[/yellow]")

    return recovered_count
