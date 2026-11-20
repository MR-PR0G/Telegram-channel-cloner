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

async def search_dialogs(client: TelegramClient, dialogs: List[Dialog], prompt_text: str):
    while True:
        search_query = console.input(f"\n[bold cyan]{prompt_text}[/bold cyan]").strip()
        if not search_query:
            console.print("[red]Search query cannot be empty.[/red]")
            continue

        query_lower = search_query.lower()
        matches = []

        for dialog in dialogs:
            title = get_entity_display_name(dialog).lower()
            username = get_entity_username(dialog).lower()
            is_saved = "saved" in title or (dialog.entity and getattr(dialog.entity, 'is_self', False))

            if query_lower in title or query_lower in username or (is_saved and "saved" in query_lower):
                matches.append(dialog)

        # Fallback: check direct ID or @username resolution
        if not matches and (search_query.startswith("-100") or search_query.lstrip("-").isdigit() or search_query.startswith("@") or "t.me/" in search_query):
            try:
                target = search_query.split("t.me/")[-1].replace("/", "") if "t.me/" in search_query else search_query
                target = int(target) if target.lstrip("-").isdigit() else target
                entity = await client.get_entity(target)
                if entity:
                    matches.append(entity)
            except Exception:
                pass

        if not matches:
            console.print("[yellow]No matching dialogs found. Try another query or provide an exact ID/@username.[/yellow]")
            continue

        console.print(f"\n[bold green]Matches for '{search_query}':[/bold green]")
        for idx, match in enumerate(matches, 1):
            name_string = get_entity_display_name(match)
            username = get_entity_username(match)
            user_string = f" (@{username})" if username else ""
            match_id = getattr(match, 'id', 'N/A')
            console.print(f"[bold]{idx}[/bold]. {name_string}{user_string} [dim][ID: {match_id}][/dim]")

        selection = console.input(f"\n[bold cyan]Select entry (1-{len(matches)}) or Enter to search again: [/bold cyan]").strip()
        if not selection:
            continue

        try:
            selected_idx = int(selection) - 1
            if 0 <= selected_idx < len(matches):
                chosen = matches[selected_idx]
                logger.info(f"Selected: {get_entity_display_name(chosen)} ({getattr(chosen, 'id', 'N/A')})")
                return chosen
            else:
                console.print(f"[red]Enter a number between 1 and {len(matches)}.[/red]")
        except ValueError:
            console.print("[red]Invalid selection. Please enter a valid number.[/red]")
