import os
import python_socks
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from rich.console import Console
import config
from src.logger import get_logger

logger = get_logger()
console = Console()

def _get_proxy_type(type_str: str):
    lookup = {
        "SOCKS5": python_socks.ProxyType.SOCKS5,
        "SOCKS4": python_socks.ProxyType.SOCKS4,
        "HTTP": python_socks.ProxyType.HTTP,
    }
    return lookup.get(type_str.upper(), python_socks.ProxyType.HTTP)

async def get_authenticated_client() -> TelegramClient:
    session_path = os.path.join(config.SESSION_DIR, "cloner_session")

    if config.API_ID == 0 or not config.API_HASH:
        console.print("[bold red]API_ID and API_HASH must be configured in config.py or environment variables.[/bold red]")
        raise SystemExit(1)

    proxy_config = None
    if config.USE_PROXY:
        p_type = _get_proxy_type(config.PROXY_TYPE)
        logger.info(f"Using {config.PROXY_TYPE} proxy: {config.PROXY_HOST}:{config.PROXY_PORT}")
        proxy_config = {
            'proxy_type': p_type,
            'addr': config.PROXY_HOST,
            'port': config.PROXY_PORT,
            'username': config.PROXY_USERNAME,
            'password': config.PROXY_PASSWORD,
            'rdns': True
        }

    client = TelegramClient(
        session_path,
        config.API_ID,
        config.API_HASH,
        proxy=proxy_config,
        connection_retries=config.NETWORK_RETRIES,
        retry_delay=2,
        timeout=config.NETWORK_TIMEOUT
    )

    await client.connect()

    if not await client.is_user_authorized():
        console.print("[bold yellow]Authentication required.[/bold yellow]")
        phone = console.input("[bold cyan]Enter phone number (with country code): [/bold cyan]").strip()

        try:
            await client.send_code_request(phone)
        except Exception as e:
            logger.error(f"Failed to send verification code: {e}")
            console.print(f"[bold red]Failed to send verification code: {e}[/bold red]")
            raise SystemExit(1)

        code = console.input("[bold cyan]Enter login code: [/bold cyan]").strip()

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = console.input("[bold cyan]2FA Password: [/bold cyan]", password=True)
            try:
                await client.sign_in(password=password)
            except Exception as e:
                logger.error(f"2FA sign-in failed: {e}")
                console.print(f"[bold red]2FA sign-in failed: {e}[/bold red]")
                raise SystemExit(1)
        except Exception as e:
            logger.error(f"Sign-in failed: {e}")
            console.print(f"[bold red]Sign-in failed: {e}[/bold red]")
            raise SystemExit(1)

    return client
