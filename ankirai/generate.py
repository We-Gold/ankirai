"""
Card generation via PydanticAI.
Receives list[Chunk] + Config → list[Card].
"""

from __future__ import annotations

from tqdm import tqdm
from pydantic_ai import Agent

from .models import Card, CardList, Chunk, Config


def _build_agent(config: Config) -> Agent:
    if config.provider == "gemini":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
        model = GoogleModel(config.model, provider=GoogleProvider(api_key=config.api_key))

    elif config.provider == "openai":
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        model = OpenAIModel(config.model, provider=OpenAIProvider(api_key=config.api_key))

    elif config.provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        model = AnthropicModel(config.model, api_key=config.api_key)

    elif config.provider in ("openrouter", "ollama"):
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(api_key=config.api_key or "ollama", base_url=config.base_url)
        model = OpenAIModel(config.model, provider=provider)

    else:
        raise ValueError(f"Unsupported provider: {config.provider!r}")

    return Agent(model, output_type=CardList, system_prompt=config.prompt)


def generate_cards(chunks: list[Chunk], config: Config) -> list[Card]:
    agent = _build_agent(config)
    all_cards: list[Card] = []

    with tqdm(chunks, desc="Generating cards", unit="chunk") as bar:
        for chunk in bar:
            prompt_text = config.prompt.replace("{{notes}}", chunk.text) if "{{notes}}" in config.prompt else chunk.text
            result = agent.run_sync(prompt_text)
            batch = result.output.cards

            for card in batch:
                card.source_file = chunk.source_file
                card.source_chunk = chunk.chunk_index
                if card.is_cloze:
                    card.back = ""

            all_cards.extend(batch)

    return all_cards
