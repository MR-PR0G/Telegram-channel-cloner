# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

from typing import List
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from src.logger import get_logger

logger = get_logger()
console = Console()

async def fetch_cached_dialogs(client: TelegramClient) -> List[Dialog]:
    logger.info("Caching all accessible user dialogs...")
    dialogs: List[Dialog] = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Fetching dialogs from Telegram...", total=None)
        
        async for dialog in client.iter_dialogs():
            dialogs.append(dialog)
            progress.update(task, description=f"Scanning dialogs... Found ({len(dialogs)})")
            
    logger.info(f"Successfully cached {len(dialogs)} dialogs.")
    return dialogs

async def search_dialogs(dialogs: List[Dialog], prompt_text: str) -> Dialog:
    while True:
        search_query = console.input(f"\n[bold cyan]{prompt_text}[/bold cyan]").strip().lower()
        if not search_query:
            console.print("[red]Search query cannot be empty.[/red]")
            continue

        matches: List[Dialog] = []
        for dialog in dialogs:
            # Check if this dialog is the user's personal "Saved Messages" chat
            is_saved_messages = False
            if dialog.entity and hasattr(dialog.entity, 'is_self') and dialog.entity.is_self:
                is_saved_messages = True
            
            title = "Saved Messages" if is_saved_messages else (dialog.name.lower() if dialog.name else "")
            
            username = ""
            if dialog.entity and hasattr(dialog.entity, 'username') and dialog.entity.username:
                username = dialog.entity.username.lower()
            
            # Match query against title, username, or explicit "saved" keyword
            if search_query in title or search_query in username or (is_saved_messages and "saved" in search_query):
                matches.append(dialog)

        if not matches:
            console.print("[yellow]No matching channels, groups or Saved Messages discovered. Try another query.[/yellow]")
            continue

        console.print(f"\n[bold green]Results matching '{search_query}':[/bold green]")
        for idx, match in enumerate(matches, 1):
            is_saved_messages = match.entity and hasattr(match.entity, 'is_self') and match.entity.is_self
            
            if is_saved_messages:
                name_string = "Saved Messages (Your Personal Chat)"
                user_string = ""
            else:
                name_string = match.name
                match_username = getattr(match.entity, 'username', None) if match.entity else None
                user_string = f" (@{match_username})" if match_username else ""
                
            console.print(f"[bold]{idx}[/bold]. {name_string}{user_string} [dim][ID: {match.id}][/dim]")

        selection = console.input(f"\n[bold cyan]Select matching entry (1-{len(matches)}) or press Enter to search again: [/bold cyan]").strip()
        if not selection:
            continue

        try:
            selected_idx = int(selection) - 1
            if 0 <= selected_idx < len(matches):
                chosen_dialog = matches[selected_idx]
                chosen_name = "Saved Messages" if (chosen_dialog.entity and hasattr(chosen_dialog.entity, 'is_self') and chosen_dialog.entity.is_self) else chosen_dialog.name
                logger.info(f"User selected dialog: {chosen_name} ({chosen_dialog.id}) for prompt: {prompt_text}")
                return chosen_dialog
            else:
                console.print(f"[red]Invalid numeric boundaries. Enter numbers between 1 and {len(matches)}.[/red]")
        except ValueError:
            console.print("[red]Invalid entry format. Provide an integer matching your selection.[/red]")