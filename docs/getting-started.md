# Getting Started with ankirai

**ankirai** transforms your notes and documents into Anki flashcard decks using an LLM of your choice.

---

## Installation

ankirai is available on [PyPI](https://pypi.org/project/ankirai/). Requires Python 3.13+.

```bash
# Recommended — installs into an isolated environment managed by uv
uv tool install ankirai

# Or with pip
pip install ankirai
```

---

## First-time Setup

Run the interactive setup wizard to configure your provider and API key:

```
$ ankirai init

Welcome to ankirai!
Default provider [gemini/openai/openrouter/ollama]: gemini
Gemini API key: ••••••••••••••••••••••••

Config saved to ~/Library/Application Support/ankirai/config.toml
Run 'ankirai generate notes.pdf' to get started.
```

Your API key is stored in a local config file with owner-only permissions (`600`) and is never logged or embedded in exported deck files.

---

## Basic Usage

Generate a deck from a single file:

```bash
ankirai generate lecture01.pdf --deck "Biochemistry"
```

This will:
1. Parse the file and extract text (using OCR for images/handwriting if vision is enabled)
2. Generate flashcards with your configured LLM
3. Export a `Biochemistry.apkg` file you can import into Anki

---

## Supported Input Formats

ankirai uses [markitdown](https://github.com/microsoft/markitdown) to parse documents. Supported formats include:

| Format | Notes |
|---|---|
| PDF | Text extraction; vision model used for scanned/image pages |
| DOCX | Full text extraction |
| PPTX | Slide text extraction |
| Markdown / plain text | Passed through directly |
| Images (PNG, JPG, etc.) | Requires a vision-capable model |
| Handwritten notes | OCR via vision model |

---

## Supported Providers

| Provider | Setup | Default model |
|---|---|---|
| **Gemini** (default) | `GEMINI_API_KEY` env var or `ankirai init` | `gemini-3.1-flash-lite` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-5.4-nano` |
| **OpenRouter** | `OPENROUTER_API_KEY` | Any model via single key |
| **Ollama** | Local server at `http://localhost:11434` | `llama4` |

> **Claude / Anthropic models**: Use OpenRouter — set `--provider openrouter --model anthropic/claude-haiku-4-5`.

Switch providers per-run with `--provider`:

```bash
ankirai generate notes.pdf --provider openai --model gpt-5.4-nano
```

---

## Review UI

Add `--review` to launch a browser-based review session before the deck is exported:

```bash
ankirai generate lecture01.pdf --deck "Biochemistry" --review
```

A local server starts at `http://localhost:5173` and your browser opens automatically. Review cards one by one or switch to the bulk table view. Only cards you accept are included in the exported file. See [Review UI reference](review-ui.md) for keyboard shortcuts and full feature details.

---

## Config File Location

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/ankirai/config.toml` |
| Linux | `~/.config/ankirai/config.toml` |
| Windows | `%APPDATA%\ankirai\config.toml` |

View your current config (with keys redacted):

```bash
ankirai config show
```

---

## Customizing the Prompt

ankirai uses a Markdown prompt file to instruct the LLM how to generate cards. Edit it globally:

```bash
ankirai prompt edit   # opens in $EDITOR
ankirai prompt show   # print the active prompt
ankirai prompt reset  # restore built-in default
```

You can also place a `ankirai_prompt.md` file alongside your input files for a per-project prompt, or pass `--prompt path/to/ankirai_prompt.md` for a single run.

---

## Directory Input

Pass a folder instead of individual files to process everything inside it at once:

```bash
ankirai generate lectures/ --deck "BIOL 301"
```

ankirai recursively scans the folder, skips unsupported file types (with a log message), and excludes any `ankirai_prompt.md` files so a local prompt is never turned into flashcards.

---

## Incremental Workflows

After a successful export, ankirai writes `ankirai_manifest.json` in the working directory. On subsequent runs, files whose content hasn't changed are skipped automatically:

```bash
ankirai generate lectures/ --deck "BIOL 301"   # processes all files, writes manifest
ankirai generate lectures/ --deck "BIOL 301"   # skips unchanged files
ankirai generate lectures/ --deck "BIOL 301" --force  # reprocesses everything
```

ankirai also derives stable GUIDs from each card's content, so importing multiple `.apkg` files with the same deck name into Anki is safe — Anki deduplicates on import and won't create duplicate cards.
