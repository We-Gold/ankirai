"""
Config resolution: CLI flag → env var → .env → config.toml → defaults.
This is the only module that touches os.environ, .env files, or prompt files.
"""

from __future__ import annotations

import os
import stat
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_config_dir

from .models import Config

APP_NAME = "ankirai"

DEFAULT_PROMPT = """\
You are an expert at creating Anki flashcards for university students.
Given the following lecture notes (which may be OCR'd from handwritten text), \
generate high-quality question-and-answer flashcards.

Guidelines:
- Focus on key concepts, definitions, formulas, and relationships.
- Each card should test one atomic fact or concept.
- You may use LaTeX for mathematical notation where appropriate — \
  Anki renders MathJax using \\( ... \\) for inline and \\[ ... \\] for block.

Choosing card type:
- Use BASIC (is_cloze=false) for most cards: a clear question in `front`, \
  a concise answer in `back`.
- Use CLOZE (is_cloze=true) only when a complete, meaningful sentence with a \
  blanked key term is more effective than a Q&A pair. \
  For cloze cards: `front` is the full sentence with {{c1::term}} syntax; \
  `back` should always be left blank.

- Add 1–3 short topic tags per card (e.g. ["database", "relational-algebra"]).
- Skip meta-content like dates, page numbers, or instructor names.
- Aim for 10–20 cards per chunk of notes.

<notes>
{{notes}}
</notes>
"""

DEFAULT_MODELS = {
    "gemini": "gemini-3.1-flash-lite",
    "openai": "gpt-5.4-nano",
    "anthropic": "claude-haiku-4-5-20251001",
    "openrouter": "google/gemini-3.1-flash-lite",
    "ollama": "llama4",
}

ONLINE_PROVIDERS = {"gemini", "openai", "anthropic", "openrouter"}


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


def config_path() -> Path:
    return config_dir() / "config.toml"


def prompt_path() -> Path:
    return config_dir() / "ankirai_prompt.md"


def _ensure_prompt_file() -> None:
    p = prompt_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(DEFAULT_PROMPT)


def run_init() -> None:
    """Interactive first-time setup. Writes config.toml."""
    print("Welcome to ankirai!")
    providers = ["gemini", "openai", "anthropic", "openrouter", "ollama"]
    provider_list = "/".join(providers)
    provider = input(f"Default provider [{provider_list}]: ").strip() or "gemini"
    if provider not in providers:
        print(f"Unknown provider '{provider}', defaulting to gemini.")
        provider = "gemini"

    api_key = ""
    if provider != "ollama":
        import getpass
        label = f"{provider.capitalize()} API key"
        api_key = getpass.getpass(f"{label}: ").strip()

    base_url = ""
    default_model = DEFAULT_MODELS.get(provider, "")
    if provider == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif provider == "ollama":
        base_url = "http://localhost:11434"
        default_model = input(f"Ollama model [{default_model}]: ").strip() or default_model

    cfg_dir = config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = config_path()

    toml_lines = [
        "[providers]",
        f'default = "{provider}"',
        "",
        f"[providers.{provider}]",
    ]
    if api_key:
        toml_lines.append(f'api_key = "{api_key}"')
    if base_url:
        toml_lines.append(f'base_url = "{base_url}"')
    if default_model:
        toml_lines.append(f'default_model = "{default_model}"')

    cfg_file.write_text("\n".join(toml_lines) + "\n")
    cfg_file.chmod(stat.S_IRUSR | stat.S_IWUSR)

    _ensure_prompt_file()

    print(f"\nConfig saved to {cfg_file}")
    print("Run 'ankirai generate notes.pdf' to get started.")


def load_config(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    vision: bool | None = None,
    batch_size: int | None = None,
    prompt_file: str | None = None,
    parsing_model: str | None = None,
) -> Config:
    """Build a fully resolved Config from all priority sources."""
    load_dotenv()

    # Read config.toml if it exists
    toml: dict = {}
    cfg = config_path()
    if cfg.exists():
        with open(cfg, "rb") as f:
            toml = tomllib.load(f)

    providers_section = toml.get("providers", {})
    generation_section = toml.get("generation", {})

    # Resolve provider
    resolved_provider = (
        provider
        or os.environ.get("ANKIRAI_PROVIDER")
        or providers_section.get("default", "gemini")
    )

    provider_cfg = providers_section.get(resolved_provider, {})

    # Resolve API key
    env_key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    env_key_name = env_key_map.get(resolved_provider, "ANKIRAI_API_KEY")
    resolved_api_key = (
        api_key
        or os.environ.get(env_key_name, "")
        or provider_cfg.get("api_key", "")
    )

    # Resolve model
    resolved_model = (
        model
        or os.environ.get("ANKIRAI_MODEL")
        or provider_cfg.get("default_model")
        or DEFAULT_MODELS.get(resolved_provider, "gemini-3.1-flash-lite")
    )

    # Resolve base_url
    default_base_urls = {
        "openrouter": "https://openrouter.ai/api/v1",
        "ollama": "http://localhost:11434",
    }
    resolved_base_url = provider_cfg.get("base_url", default_base_urls.get(resolved_provider, ""))

    # Resolve vision
    default_vision = resolved_provider in ONLINE_PROVIDERS
    if vision is not None:
        resolved_vision = vision
    else:
        resolved_vision = provider_cfg.get("vision", default_vision)

    # Resolve batch_size
    is_local = resolved_provider == "ollama"
    default_batch = generation_section.get(
        "batch_size_local" if is_local else "batch_size_online",
        5 if is_local else 15,
    )
    resolved_batch = batch_size or default_batch

    # Resolve parsing_model
    resolved_parsing_model = (
        parsing_model
        or os.environ.get("ANKIRAI_PARSING_MODEL", "")
        or generation_section.get("parsing_model", "")
    )

    # Resolve prompt
    _ensure_prompt_file()
    if prompt_file:
        active_prompt = Path(prompt_file).read_text()
    else:
        local_prompt = Path("ankirai_prompt.md")
        if local_prompt.exists():
            active_prompt = local_prompt.read_text()
        else:
            global_prompt = prompt_path()
            active_prompt = global_prompt.read_text() if global_prompt.exists() else DEFAULT_PROMPT

    return Config(
        provider=resolved_provider,
        model=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
        vision=resolved_vision,
        parsing_model=resolved_parsing_model,
        batch_size=resolved_batch,
        prompt=active_prompt,
    )
