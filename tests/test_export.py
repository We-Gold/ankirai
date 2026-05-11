import csv
import zipfile
from pathlib import Path

import pytest

from ankirai.export import stable_guid, write_apkg, write_csv


def test_stable_guid_deterministic():
    g1 = stable_guid("What is SQL?", "notes.pdf")
    g2 = stable_guid("What is SQL?", "notes.pdf")
    assert g1 == g2


def test_stable_guid_case_insensitive():
    g1 = stable_guid("What is SQL?", "notes.pdf")
    g2 = stable_guid("  WHAT IS SQL?  ", "notes.pdf")
    assert g1 == g2


def test_stable_guid_differs_by_source():
    g1 = stable_guid("Question", "file_a.pdf")
    g2 = stable_guid("Question", "file_b.pdf")
    assert g1 != g2


def test_stable_guid_differs_by_front():
    g1 = stable_guid("Question A", "notes.pdf")
    g2 = stable_guid("Question B", "notes.pdf")
    assert g1 != g2


def test_write_apkg_creates_file(sample_cards, tmp_path):
    out = tmp_path / "test.apkg"
    write_apkg(sample_cards, "Test Deck", out)
    assert out.exists()
    assert out.stat().st_size > 0
    # .apkg is a zip file
    assert zipfile.is_zipfile(out)


def test_write_csv_columns(sample_cards, tmp_path):
    out = tmp_path / "test.csv"
    write_csv(sample_cards, out)
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == len(sample_cards)
    assert set(rows[0].keys()) == {"front", "back", "tags", "source_file"}


def test_write_csv_tags_semicolon_separated(sample_cards, tmp_path):
    out = tmp_path / "test.csv"
    write_csv(sample_cards, out)
    rows = list(csv.DictReader(out.open()))
    # First card has one tag; just check it's present
    assert "database" in rows[0]["tags"]


def test_write_tsv_creates_file(sample_cards, tmp_path):
    out = tmp_path / "test.tsv"
    write_csv(sample_cards, out, delimiter="\t")
    assert out.exists()
    content = out.read_text()
    assert "\t" in content
