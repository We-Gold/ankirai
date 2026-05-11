"""Tests for config resolution priority chain."""

from unittest.mock import patch

import pytest

from ankirai.config import load_config


def _patch_no_config(tmp_path):
    """Return a context manager that makes config_path() point to a nonexistent file."""
    return patch("ankirai.config.config_path", return_value=tmp_path / "config.toml")


def _patch_prompt(tmp_path):
    """Silence _ensure_prompt_file and prompt_path so they don't touch the real FS."""
    prompt = tmp_path / "prompt.md"
    prompt.write_text("prompt text")
    return (
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=prompt),
    )


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """Strip all ankirai / provider env vars and redirect FS paths."""
    for var in (
        "ANKIRAI_PROVIDER",
        "ANKIRAI_MODEL",
        "ANKIRAI_PARSING_MODEL",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANKIRAI_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)  # avoid picking up a local ankirai_prompt.md


def test_default_provider_is_gemini(tmp_path):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config()
    assert cfg.provider == "gemini"


def test_cli_provider_beats_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANKIRAI_PROVIDER", "openai")
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="ollama")
    assert cfg.provider == "ollama"


def test_env_var_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "my-key")
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="gemini")
    assert cfg.api_key == "my-key"


def test_cli_api_key_beats_env(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="gemini", api_key="cli-key")
    assert cfg.api_key == "cli-key"


@pytest.mark.parametrize("provider", ["gemini", "openai", "openrouter"])
def test_online_providers_default_vision_true(tmp_path, provider):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider=provider)
    assert cfg.vision is True


def test_ollama_defaults_vision_false(tmp_path):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="ollama")
    assert cfg.vision is False


def test_batch_size_online_default(tmp_path):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="gemini")
    assert cfg.batch_size == 15


def test_batch_size_local_default(tmp_path):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="ollama")
    assert cfg.batch_size == 5


def test_openrouter_gets_base_url(tmp_path):
    with (
        _patch_no_config(tmp_path),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="openrouter")
    assert cfg.base_url == "https://openrouter.ai/api/v1"


def test_cli_kwarg_overrides_config_file(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[providers]\ndefault = "openai"\n')
    with (
        patch("ankirai.config.config_path", return_value=cfg_file),
        patch("ankirai.config._ensure_prompt_file"),
        patch("ankirai.config.prompt_path", return_value=tmp_path / "p.md"),
    ):
        cfg = load_config(provider="ollama")
    assert cfg.provider == "ollama"
