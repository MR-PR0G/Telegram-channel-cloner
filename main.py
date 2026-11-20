import asyncio
import sys
import argparse
from rich.console import Console
import config
from src.logger import setup_logger
from src.authentication import get_authenticated_client
from src.dialog_search import fetch_cached_dialogs, search_dialogs
from src.cloner import execute_cloning, execute_retry_failed_messages
from src.progress import (
    load_progress, clear_progress, get_failed_messages_count, clear_failed_messages
)
from src.utils import get_entity_display_name, get_entity_username

console = Console()

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram Channel Cloner")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed messages from failed_messages.json")
    parser.add_argument("--resume", action="store_true", help="Automatically resume previous session")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh without prompting to resume")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size before pausing for cooldown")
    parser.add_argument("--batch-cooldown", type=float, default=None, help="Cooldown duration in seconds after each batch")
    parser.add_argument("--min-id", type=int, default=None, help="Minimum message ID to clone")
    parser.add_argument("--max-id", type=int, default=None, help="Maximum message ID to clone")
    return parser.parse_args()

async def async_main() -> None:
    args = parse_arguments()
    setup_logger()

    if args.batch_size is not None:
        config.BATCH_SIZE = args.batch_size
    if args.batch_cooldown is not None:
        config.BATCH_COOLDOWN_SECONDS = args.batch_cooldown
    if args.min_id is not None:
        config.MIN_MSG_ID = args.min_id
    if args.max_id is not None:
        config.MAX_MSG_ID = args.max_id

    client = await get_authenticated_client()

    saved_session = load_progress()
    source_dialog = None
    dest_dialog = None
    resume_from_id = 0
    initial_copied_count = 0
    use_resume = False

    failed_count = get_failed_messages_count()

    # Retry failed messages workflow
    if args.retry_failed or (failed_count > 0 and not args.resume):
        prompt_retry = args.retry_failed
        if not prompt_retry:
            choice = console.input(
                f"[bold yellow]Found {failed_count} failed message(s) in failed_messages.json. Retry them now? [y/N]: [/bold yellow]"
            ).strip().lower()
            prompt_retry = choice in ("y", "yes")

        if prompt_retry:
            if saved_session:
                try:
                    source_dialog = await client.get_entity(saved_session.source_id)
                    dest_dialog = await client.get_entity(saved_session.destination_id)
                except Exception:
                    source_dialog = None
                    dest_dialog = None

            if not source_dialog or not dest_dialog:
                console.print("[cyan]Select channels for retrying failed messages:[/cyan]")
                cached_dialogs = await fetch_cached_dialogs(client)
                source_dialog = await search_dialogs(client, cached_dialogs, "Select source channel: ")
                dest_dialog = await search_dialogs(client, cached_dialogs, "Select destination channel: ")

            src_title = get_entity_display_name(source_dialog)
            dst_title = get_entity_display_name(dest_dialog)
            src_user = get_entity_username(source_dialog)
            dst_user = get_entity_username(dest_dialog)

            await execute_retry_failed_messages(
                client=client,
                source_id=source_dialog.id,
                destination_id=dest_dialog.id,
                source_title=src_title,
                destination_title=dst_title,
                source_username=src_user,
                dest_username=dst_user
            )

            if args.retry_failed:
                await client.disconnect()
                return

    # Normal cloning workflow
    if saved_session and not args.no_resume:
        console.print("[bold yellow]Previous session found:[/bold yellow]")
        console.print(f"  Source: {saved_session.source_title} -> Destination: {saved_session.destination_title}")
        console.print(f"  Last message ID: {saved_session.last_source_msg_id} | Copied count: {saved_session.copied_count}")

        if args.resume or config.AUTO_RESUME:
            use_resume = True
        else:
            selection = console.input("[bold cyan]Resume previous session? [Y/n]: [/bold cyan]").strip().lower()
            if selection in ("", "y", "yes"):
                use_resume = True

        if use_resume:
            resume_from_id = saved_session.last_source_msg_id
            initial_copied_count = saved_session.copied_count
            try:
                source_dialog = await client.get_entity(saved_session.source_id)
                dest_dialog = await client.get_entity(saved_session.destination_id)
            except Exception:
                console.print("[bold red]Could not resolve saved entities. Starting new selection...[/bold red]")
                use_resume = False

    if not use_resume:
        clear_progress()
        cached_dialogs = await fetch_cached_dialogs(client)
        source_dialog = await search_dialogs(client, cached_dialogs, "Search source channel: ")
        dest_dialog = await search_dialogs(client, cached_dialogs, "Search destination channel: ")

    source_title = get_entity_display_name(source_dialog)
    dest_title = get_entity_display_name(dest_dialog)
    source_username = get_entity_username(source_dialog)
    dest_username = get_entity_username(dest_dialog)

    try:
        await execute_cloning(
            client=client,
            source_id=source_dialog.id,
            destination_id=dest_dialog.id,
            source_title=source_title,
            destination_title=dest_title,
            source_username=source_username,
            dest_username=dest_username,
            resume_from_msg_id=resume_from_id,
            initial_copied=initial_copied_count
        )

        clear_progress()
        console.print("\n[bold green]Cloning completed successfully.[/bold green]")

    except (KeyboardInterrupt, SystemExit):
        console.print("\n[bold yellow]Operation stopped. Progress saved.[/bold yellow]")
    finally:
        remaining_failed = get_failed_messages_count()
        if remaining_failed > 0:
            console.print(f"[bold red]Failed messages remaining: {remaining_failed}[/bold red]")
            console.print("Run with --retry-failed to re-attempt failed messages.")

        await client.disconnect()

def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exited.[/bold yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()
