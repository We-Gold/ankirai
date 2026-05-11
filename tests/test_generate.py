from unittest.mock import MagicMock, patch

import pytest

from ankirai.generate import generate_cards
from ankirai.models import Card, CardList, Chunk, Config


@pytest.fixture
def config() -> Config:
    return Config(
        provider="gemini",
        model="gemini-3.1-flash-lite",
        api_key="test-key",
        batch_size=15,
        prompt="Generate cards:\n\n{{notes}}",
    )


@pytest.fixture
def chunks() -> list[Chunk]:
    return [
        Chunk(text="Databases store data.", source_file="notes.pdf", chunk_index=0),
        Chunk(text="SQL queries tables.", source_file="notes.pdf", chunk_index=1),
    ]


def _make_mock_result(cards: list[Card]):
    result = MagicMock()
    result.output = CardList(cards=cards)
    return result


def test_generate_attaches_metadata(config, chunks):
    def fresh_cards():
        return _make_mock_result([Card(front="Q1?", back="A1"), Card(front="Q2?", back="A2")])

    with patch("ankirai.generate._build_agent") as mock_build:
        agent = MagicMock()
        agent.run_sync.side_effect = lambda _: fresh_cards()
        mock_build.return_value = agent

        result = generate_cards(chunks, config)

    assert len(result) == 4  # 2 cards × 2 chunks
    assert all(c.source_file == "notes.pdf" for c in result)
    assert result[0].source_chunk == 0
    assert result[2].source_chunk == 1


def test_generate_calls_agent_per_chunk(config, chunks):
    fake_cards = [Card(front="Q?", back="A")]

    with patch("ankirai.generate._build_agent") as mock_build:
        agent = MagicMock()
        agent.run_sync.return_value = _make_mock_result(fake_cards)
        mock_build.return_value = agent

        generate_cards(chunks, config)

    assert agent.run_sync.call_count == len(chunks)


def test_generate_prompt_substitution(config, chunks):
    """Verify {{notes}} is replaced with chunk text in the prompt passed to the agent."""
    fake_cards = [Card(front="Q?", back="A")]
    captured_prompts = []

    def capture_run_sync(prompt):
        captured_prompts.append(prompt)
        return _make_mock_result(fake_cards)

    with patch("ankirai.generate._build_agent") as mock_build:
        agent = MagicMock()
        agent.run_sync.side_effect = capture_run_sync
        mock_build.return_value = agent

        generate_cards(chunks, config)

    assert "{{notes}}" not in captured_prompts[0]
    assert chunks[0].text in captured_prompts[0]
