from typing import List
from telethon import TelegramClient
from telethon.tl.custom import Dialog
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from src.logger import get_logger
from src.utils import get_entity_display_name, get_entity_username

logger = get_logger()
console = Console()

async def fetch_cached_dialogs(client: TelegramClient) -> List[Dialog]:
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

    logger.info(f"Cached {len(dialogs)} dialogs.")
    return dialogs

async def search_dialogs(dialogs: List[Dialog], prompt_text: str) -> Dialog:
    while True:
        search_query = console.input(f"\n[bold cyan]{prompt_text}[/bold cyan]").strip().lower()
        if not search_query:
            console.print("[red]Search query cannot be empty.[/red]")
            continue

        matches: List[Dialog] = []
        for dialog in dialogs:
            title = get_entity_display_name(dialog).lower()
            username = get_entity_username(dialog).lower()

            is_saved = "saved" in title or (dialog.entity and getattr(dialog.entity, 'is_self', False))

            if search_query in title or search_query in username or (is_saved and "saved" in search_query):
                matches.append(dialog)

        if not matches:
            console.print("[yellow]No matching dialogs found. Try another query.[/yellow]")
            continue

        console.print(f"\n[bold green]Matches for '{search_query}':[/bold green]")
        for idx, match in enumerate(matches, 1):
            name_string = get_entity_display_name(match)
            username = get_entity_username(match)
            user_string = f" (@{username})" if username else ""
            console.print(f"[bold]{idx}[/bold]. {name_string}{user_string} [dim][ID: {match.id}][/dim]")

        selection = console.input(f"\n[bold cyan]Select entry (1-{len(matches)}) or Enter to search again: [/bold cyan]").strip()
        if not selection:
            continue

        try:
            selected_idx = int(selection) - 1
            if 0 <= selected_idx < len(matches):
                chosen = matches[selected_idx]
                logger.info(f"Selected: {get_entity_display_name(chosen)} ({chosen.id})")
                return chosen
            else:
                console.print(f"[red]Enter a number between 1 and {len(matches)}.[/red]")
        except ValueError:
            console.print("[red]Invalid selection. Please enter a valid number.[/red]")
