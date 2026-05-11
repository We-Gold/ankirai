"""
Deck and file output.
Receives list[Card] → .apkg or .csv/.tsv file.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import click
import genanki

from .models import Card


def stable_guid(front: str, source_file: str) -> int:
    key = f"{source_file}::{front.strip().lower()}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


_BASIC_MODEL = genanki.Model(
    1607392319,
    "ankirai Basic",
    fields=[{"name": "Front"}, {"name": "Back"}, {"name": "Tags"}],
    templates=[{
        "name": "Card 1",
        "qfmt": "{{Front}}",
        "afmt": "{{FrontSide}}<hr id='answer'>{{Back}}",
    }],
)


def write_apkg(cards: list[Card], deck_name: str, output_path: Path) -> None:
    deck = genanki.Deck(2059400110, deck_name)

    for card in cards:
        guid = stable_guid(card.front, card.source_file)

        if card.is_cloze:
            note = genanki.Note(
                model=genanki.CLOZE_MODEL,
                fields=[card.front, ""],
                tags=card.tags,
                guid=guid,
            )
        else:
            note = genanki.Note(
                model=_BASIC_MODEL,
                fields=[card.front, card.back, ""],
                tags=card.tags,
                guid=guid,
            )

        deck.add_note(note)

    package = genanki.Package(deck)
    package.write_to_file(str(output_path))
    click.echo(f"Exported {len(cards)} cards to {output_path}")


def write_csv(cards: list[Card], output_path: Path, delimiter: str = ",") -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(["front", "back", "tags", "source_file"])
        for card in cards:
            writer.writerow([
                card.front,
                card.back,
                ";".join(card.tags),
                card.source_file,
            ])
    click.echo(f"Exported {len(cards)} cards to {output_path}")
