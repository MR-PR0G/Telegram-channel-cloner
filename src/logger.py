# Copyright (c) 2026 https://github.com/MR-PR0G
# Licensed under the MIT License. See LICENSE file in the project root.
# SPDX-License-Identifier: MIT

import logging
import os
from datetime import datetime
import config

_logger: logging.Logger | None = None

def setup_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger_instance = logging.getLogger("TelegramCloner")
    logger_instance.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(config.LOG_DIR, f"{timestamp}.log")
    
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger_instance.addHandler(file_handler)
    
    _logger = logger_instance
    return _logger

def get_logger() -> logging.Logger:
    if _logger is None:
        return setup_logger()
    return _logger