# ankirai

**暗記 (anki)** · memorization &nbsp;·&nbsp; **雷 (rai)** · lightning

Transform your notes into Anki flashcards at lightning speed using any LLM provider.

## Installation

Requires Python 3.13+. Install with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ankirai
```

Or clone and run locally:

```bash
git clone <repo>
cd ankirai
uv run ankirai --help
```

## Quick start

```bash
ankirai init                          # first-time setup: pick provider and enter API key
ankirai generate notes.pdf            # generate an Anki deck (.apkg)
ankirai generate notes.pdf --review   # review cards in the browser before exporting
```

## Commands

### `ankirai init`

Interactive setup. Stores your provider and API key in a platform config file (chmod 600). Run once before your first `generate`.

### `ankirai generate [OPTIONS] INPUTS...`

Parse one or more input files and generate an Anki deck.

| Option | Description |
|---|---|
| `--deck`, `-d` | Deck name (default: first filename stem) |
| `--model`, `-m` | Model override |
| `--provider`, `-p` | Provider override (`gemini`, `openai`, `anthropic`, `openrouter`, `ollama`) |
| `--api-key` | API key override |
| `--format` | Output format: `apkg` (default), `csv`, `tsv` |
| `--output`, `-o` | Output file path |
| `--batch-size` | Cards per LLM request |
| `--force` | Ignore manifest; reprocess all input files |
| `--tags` | Comma-separated tags to add to all cards |
| `--vision` / `--no-vision` | Override vision capability detection |
| `--parsing-model` | Use a separate model for image/PDF parsing |
| `--prompt` | Path to a custom prompt file |
| `--review` | Open browser review UI before exporting |

### `ankirai config show`

Print current config with API keys redacted.

### `ankirai config set KEY VALUE`

Update a single config value, e.g.:

```bash
ankirai config set openai.api_key sk-...
ankirai config set providers.default anthropic
```

### `ankirai prompt show`

Print the currently active card-generation prompt.

### `ankirai prompt edit`

Open the global prompt in `$EDITOR`.

### `ankirai prompt reset`

Restore the built-in default prompt.

## Providers

| Provider | Key name | Default model |
|---|---|---|
| `gemini` | `GEMINI_API_KEY` | `gemini-3.1-flash-lite` |
| `openai` | `OPENAI_API_KEY` | `gpt-5.4-nano` |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5-20251001` |
| `openrouter` | `OPENROUTER_API_KEY` | `google/gemini-3.1-flash-lite` |
| `ollama` | *(none)* | `llama4` |

API keys can also be set via environment variables or a `.env` file in the working directory.

## Config resolution

For each setting, the first value found wins:

1. CLI flag
2. Environment variable
3. `.env` file
4. `config.toml` (platform config dir)
5. Built-in default

## Custom prompts

Prompt resolution order:

1. `--prompt <file>` flag
2. `ankirai_prompt.md` in the current working directory
3. Global prompt file (`ankirai prompt edit`)
4. Built-in default

The prompt should include `{{notes}}` where the chunk text will be substituted. Cards support LaTeX using MathJax syntax (`\(...\)` inline, `\[...\]` block). Cloze cards use `{{c1::term}}` syntax.

## Review UI

`--review` launches a local web server at `http://localhost:5173` and opens your browser.

**Card view** — keyboard shortcuts:

| Key | Action |
|---|---|
| `1` | Accept |
| `2` | Edit (inline) |
| `3` | Reject |
| `[` or `←` | Previous card |
| `]` or `→` | Next card |

**Bulk view** — shows all cards in a paginated table (50 per page). Use the "View" button on any row to jump to that card. Use "Accept all pending" to approve everything at once.

The nav bar shows "Card view" when on the bulk page and "Bulk view" when reviewing card-by-card.

Only accepted cards are included in the exported deck.

## Manifest

ankirai tracks which files have been processed in a `ankirai_manifest.json` in the working directory. Re-running `generate` on the same inputs skips unchanged files. Use `--force` to reprocess everything.

## Supported input formats

Anything [markitdown](https://github.com/microsoft/markitdown) can parse: PDF, DOCX, PPTX, images (with vision-capable models), plain text, Markdown, and more.
