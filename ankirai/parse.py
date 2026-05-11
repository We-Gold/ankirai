"""
Document parsing and chunking.
Wraps markitdown; returns list[Chunk] ready for generate.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from .models import Chunk, Config


def chunk_markdown(text: str, max_chars: int = 3000) -> list[str]:
    heading_pattern = re.compile(r"(?=^#{1,3} )", re.MULTILINE)
    parts = heading_pattern.split(text)
    parts = [p.strip() for p in parts if p.strip()]

    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) > max_chars and current:
            chunks.append(current.strip())
            current = part
        else:
            current += "\n\n" + part if current else part

    if current.strip():
        chunks.append(current.strip())

    # Fall back to fixed-size windows if no headings produced usable splits
    if not chunks or all(len(c) > max_chars for c in chunks):
        chunks = []
        for i in range(0, len(text), max_chars):
            piece = text[i : i + max_chars].strip()
            if piece:
                chunks.append(piece)

    return chunks


def parse_file(file_path: Path, config: Config) -> list[Chunk]:
    """Parse a document into Chunks using markitdown."""
    from markitdown import MarkItDown

    click.echo(f"Parsing {file_path.name}...", nl=False)

    if config.vision and config.api_key:
        from openai import OpenAI
        vision_model = config.parsing_model or config.model
        base_url = config.base_url or None

        # Gemini OpenAI-compat endpoint
        if config.provider == "gemini":
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

        openai_client = OpenAI(api_key=config.api_key, base_url=base_url)
        md = MarkItDown(llm_client=openai_client, llm_model=vision_model)
    else:
        if not config.vision:
            click.echo("  [vision disabled — image content will be skipped]", err=True)
        md = MarkItDown()

    result = md.convert(str(file_path))
    raw_text = result.text_content
    text_chunks = chunk_markdown(raw_text)

    click.echo(f" done ({len(text_chunks)} chunk{'s' if len(text_chunks) != 1 else ''})")

    return [
        Chunk(text=text, source_file=file_path.name, chunk_index=i)
        for i, text in enumerate(text_chunks)
    ]
