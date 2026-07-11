# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import asyncio
import sys
from rich.console import Console
import config
from src.logger import setup_logger
from src.authentication import get_authenticated_client
from src.dialog_search import fetch_cached_dialogs, search_dialogs
from src.cloner import execute_cloning
from src.progress import load_progress, clear_progress, get_failed_messages_count, clear_failed_messages

console = Console()

async def async_main() -> None:
    setup_logger()
    client = await get_authenticated_client()

    saved_session = load_progress()
    source_dialog = None
    dest_dialog = None
    
    resume_from_id = 0
    initial_copied_count = 0
    
    use_resume = False

    if saved_session:
        console.print(f"[bold yellow]Previous session found.[/bold yellow]")
        console.print(f"Source: {saved_session.source_title} -> Destination: {saved_session.destination_title}")
        console.print(f"Last copied message ID: {saved_session.last_source_msg_id}, Copied Count: {saved_session.copied_count}")
        
        if config.AUTO_RESUME:
            use_resume = True
        else:
            selection = console.input("[bold cyan]Continue previous operational sequence? [Y/n]: [/bold cyan]").strip().lower()
            if selection in ("", "y", "yes"):
                use_resume = True

        if use_resume:
            resume_from_id = saved_session.last_source_msg_id
            initial_copied_count = saved_session.copied_count
            
            try:
                source_dialog = await client.get_entity(saved_session.source_id)
                dest_dialog = await client.get_entity(saved_session.destination_id)
            except Exception:
                console.print("[bold red]Failed fetching configuration references via historical parameters. Restarting configuration selection...[/bold red]")
                use_resume = False

    if not use_resume:
        clear_progress()
        clear_failed_messages()
        
        cached_dialogs = await fetch_cached_dialogs(client)
        source_dialog = await search_dialogs(cached_dialogs, "Search source channel: ")
        dest_dialog = await search_dialogs(cached_dialogs, "Search destination channel: ")

    source_username = getattr(source_dialog.entity, 'username', '') or '' if hasattr(source_dialog, 'entity') else ''
    dest_username = getattr(dest_dialog.entity, 'username', '') or '' if hasattr(dest_dialog, 'entity') else ''

    try:
        await execute_cloning(
            client=client,
            source_id=source_dialog.id,
            destination_id=dest_dialog.id,
            source_title=source_dialog.title if hasattr(source_dialog, 'title') else source_dialog.name,
            destination_title=dest_dialog.title if hasattr(dest_dialog, 'title') else dest_dialog.name,
            source_username=source_username,
            dest_username=dest_username,
            resume_from_msg_id=resume_from_id,
            initial_copied=initial_copied_count
        )
        
        clear_progress()
        console.print("\n[bold green]Clone operations finished successfully.[/bold green]")
        
    except (KeyboardInterrupt, SystemExit):
        console.print("\n[bold yellow]Operation suspended by manual request. Saving progress matrix state cleanly.[/bold yellow]")
    finally:
        failed_count = get_failed_messages_count()
        if failed_count > 0:
            console.print(f"[bold red]Failed messages: {failed_count}[/bold red]")
            console.print("Individual missing elements details logged completely to failed_messages.json")
        
        await client.disconnect()

def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Application aborted successfully.[/bold yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()