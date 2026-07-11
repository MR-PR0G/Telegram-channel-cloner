# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import os
import python_socks
from telethon import TelegramClient
from rich.console import Console
import config
from src.logger import get_logger

logger = get_logger()
console = Console()

async def get_authenticated_client() -> TelegramClient:
    session_path = os.path.join(config.SESSION_DIR, "cloner_session")
    
    if config.API_ID == 0 or not config.API_HASH:
        console.print("[bold red]Error: API_ID and API_HASH must be configured inside config.py before launching.[/bold red]")
        logger.error("API_ID or API_HASH missing in config.py")
        raise SystemExit(1)

    proxy_config = None
    if config.USE_PROXY:
        logger.info(f"Configuring HTTP Proxy: {config.PROXY_HOST}:{config.PROXY_PORT}")
        proxy_config = {
            'proxy_type': python_socks.ProxyType.HTTP,
            'addr': config.PROXY_HOST,
            'port': config.PROXY_PORT,
            'username': config.PROXY_USERNAME,
            'password': config.PROXY_PASSWORD,
            'rdns': True
        }

    # Enhanced configuration with absolute connection constraints and timeouts
    client = TelegramClient(
        session_path, 
        config.API_ID, 
        config.API_HASH,
        proxy=proxy_config,
        connection_retries=config.NETWORK_RETRIES,
        retry_delay=2,
        timeout=config.NETWORK_TIMEOUT
    )
    
    logger.info("Initializing Telegram Client with strict network configuration...")
    await client.connect()

    if not await client.is_user_authorized():
        logger.info("Session unauthorized. Commencing login flow.")
        console.print("[bold yellow]Authentication required.[/bold yellow]")
        
        phone = console.input("[bold cyan]Enter your Phone Number (with country code): [/bold cyan]")
        
        try:
            sent_code = await client.send_code_request(phone)
            logger.info(f"Code sent to phone: {phone}")
        except Exception as e:
            logger.error(f"Failed sending code request: {e}")
            console.print(f"[bold red]Failed to send verification code: {e}[/bold red]")
            raise SystemExit(1)

        code = console.input("[bold cyan]Enter the Login Code received: [/bold cyan]")
        
        try:
            await client.sign_in(phone, code)
            logger.info("Sign in successful.")
        except Exception as e:
            from telethon.errors import SessionPasswordNeededError
            if isinstance(e, SessionPasswordNeededError):
                logger.info("2FA Password required.")
                password = console.input("[bold cyan]2FA Password Enabled. Enter Password: [/bold cyan]", password=True)
                try:
                    await client.sign_in(password=password)
                    logger.info("Sign in successful with 2FA verification.")
                except Exception as e2:
                    logger.error(f"Authentication failure using 2FA: {e2}")
                    console.print(f"[bold red]Authentication failed: {e2}[/bold red]")
                    raise SystemExit(1)
            else:
                logger.error(f"Authentication failed: {e}")
                console.print(f"[bold red]Authentication failed: {e}[/bold red]")
                raise SystemExit(1)

    logger.info("Telegram client successfully authenticated.")
    return client