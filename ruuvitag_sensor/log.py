"""
Module level logging configuration for ruuvitag_sensor package.

This module provides:
1. A root logger for the package with default ERROR level file logging
2. A function to enable console output, primarily for CLI usage

Note: Applications using this package as a library should configure their own logging
rather than relying on this module's configuration.
"""

import logging

# Create the package's root logger
log = logging.getLogger("ruuvitag_sensor")
log.setLevel(logging.INFO)

# Configure file logging for errors
file_handler = logging.FileHandler("ruuvitag_sensor.log")
file_handler.setLevel(logging.ERROR)

# Set up a standard logging format with timestamp, logger name, level and message
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
log.addHandler(file_handler)


def enable_console(level: int = logging.INFO) -> None:
    """Enable console logging for the package.

    This function is primarily intended for command-line usage of the package.
    If the requested level is DEBUG, it will also set the root logger's level to DEBUG.
    The function ensures only one console handler is added.

    Args:
        level: The logging level for console output. Defaults to INFO.
    """
    if level < logging.INFO:
        log.setLevel(level)

    if len(log.handlers) != 2:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        log.addHandler(console_handler)
