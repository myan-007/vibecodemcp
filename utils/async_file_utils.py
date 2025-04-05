#!/usr/bin/env python3

import os
from typing import List, Literal

import anyio

# Define OpenTextMode and OpenBinaryMode similar to what anyio uses
OpenTextMode = Literal[
    "r", "r+", "+r", "rt", "rt+", "r+t", "+rt", "tr", "tr+", "t+r",
    "w", "w+", "+w", "wt", "wt+", "w+t", "+wt", "tw", "tw+", "t+w",
    "a", "a+", "+a", "at", "at+", "a+t", "+at", "ta", "ta+", "t+a",
]
OpenBinaryMode = Literal[
    "rb", "rb+", "r+b", "+rb", "br", "br+", "b+r",
    "wb", "wb+", "w+b", "+wb", "bw", "bw+", "b+w",
    "ab", "ab+", "a+b", "+ab", "ba", "ba+", "b+a",
]

async def async_open_text(
    file_path: str,
    mode: OpenTextMode = "r",
    encoding: str = "utf-8",
    errors: str = "replace",
) -> str:
    async with await anyio.open_file(
        file_path, mode, encoding=encoding, errors=errors
    ) as f:
        return await f.read()

async def async_readlines(
    file_path: str, encoding: str = "utf-8", errors: str = "replace"
) -> List[str]:
    async with await anyio.open_file(
        file_path, "r", encoding=encoding, errors=errors
    ) as f:
        return await f.readlines()

async def async_write_text(
    file_path: str,
    content: str,
    mode: OpenTextMode = "w",
    encoding: str = "utf-8",
) -> None:
    async with await anyio.open_file(
        file_path, mode, encoding=encoding, newline=""
    ) as f:
        await f.write(content)
