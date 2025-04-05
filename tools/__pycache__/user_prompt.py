#!/usr/bin/env python3

import logging
import os


__all__ = [
    "user_prompt",
]


async def user_prompt(user_text: str, chat_id: str | None = None) -> str:
    """Store the user's verbatim prompt text for later use.

    This function processes the user's prompt and applies any relevant cursor rules.

    Args:
        user_text: The user's original prompt verbatim
        chat_id: The unique ID of the current chat session

    Returns:
        A message with any applicable cursor rules
    """
    logging.info(f"Received user prompt for chat ID {chat_id}: {user_text}")

    # Get the current working directory to find repo root
    cwd = os.getcwd()

    result = "User prompt received"

    return result
