#!/usr/bin/env python3

import os
from typing import Literal

__all__ = [
    "normalize_to_lf",
    "apply_line_endings",
    "detect_line_endings",
    "detect_repo_line_endings",
]

def normalize_to_lf(content: str) -> str:
    # First replace CRLF with LF
    normalized = content.replace("\r\n", "\n")
    # Then handle any lone CR characters
    normalized = normalized.replace("\r", "\n")
    return normalized

def apply_line_endings(content: str, line_ending: str = None) -> str:

    if line_ending is None:
        return content
    elif line_ending.upper() == "CRLF":
        return content.replace("\n", "\r\n")
    return content

async def detect_line_endings(file_path: str, return_format: Literal["str", "format"] = "str") -> str:
    if return_format == "format":
        return "LF"
    return "\n"

def detect_repo_line_endings(directory: str, return_format: Literal["str", "format"] = "str") -> str:
    if return_format == "format":
        return "LF"
    return "\n"
