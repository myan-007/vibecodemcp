#!/usr/bin/env python3

import os
from typing import Optional, Tuple
import anyio

__all__ = [
    "check_file_path_and_permissions",
    "check_git_tracking_for_existing_file",
    "ensure_directory_exists",
    "write_text_content",
    "async_open_text",
]

async def check_file_path_and_permissions(file_path: str) -> Tuple[bool, Optional[str]]:
    # Check that the path is absolute
    if not os.path.isabs(file_path):
        return False, f"File path must be absolute, not relative: {file_path}"
    return True, None

async def check_git_tracking_for_existing_file(file_path: str, chat_id: str = "") -> Tuple[bool, Optional[str]]:
    return True, None

def ensure_directory_exists(file_path: str) -> None:
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

async def async_open_text(file_path: str, mode="r", encoding="utf-8", errors="replace") -> str:

    async with await anyio.open_file(file_path, mode, encoding=encoding, errors=errors) as f:
        return await f.read()

async def write_text_content(file_path: str, content: str, encoding="utf-8", line_endings=None) -> None:
    ensure_directory_exists(file_path)
    async with await anyio.open_file(file_path, "w", encoding=encoding, newline="") as f:
        await f.write(content)
