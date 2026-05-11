import pytest
from ankirai.models import Card, Config, Chunk


@pytest.fixture
def sample_config() -> Config:
    return Config(
        provider="gemini",
        model="gemini-3.1-flash-lite",
        api_key="test-key",
        vision=True,
        batch_size=15,
        prompt="Generate cards for:\n\n{{notes}}",
    )


@pytest.fixture
def sample_cards() -> list[Card]:
    return [
        Card(front="What is a primary key?", back="A unique identifier for a row.", tags=["database"], source_file="notes.pdf"),
        Card(front="The {{c1::selection}} operator filters rows.", back="", tags=["relational-algebra"], is_cloze=True, source_file="notes.pdf"),
        Card(front="What is normalization?", back="Organizing a DB to reduce redundancy.", tags=["database"], source_file="notes.pdf"),
    ]


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    return [
        Chunk(text="# Databases\nA database is an organized collection of data.", source_file="notes.pdf", chunk_index=0),
        Chunk(text="# SQL\nSELECT retrieves rows from a table.", source_file="notes.pdf", chunk_index=1),
    ]
