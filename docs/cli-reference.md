# CLI Reference

## `ankirai init`

Interactive first-time setup. Prompts for a provider and API key, then writes `config.toml` with owner-only permissions.

```bash
ankirai init
```

---

## `ankirai generate`

Parse one or more input files and export an Anki deck.

```bash
ankirai generate <inputs>... [options]
```

### Arguments

| Argument | Description |
|---|---|
| `inputs` | One or more file or directory paths to parse. Directories are scanned recursively; unsupported file types and `ankirai_prompt.md` files are excluded automatically. |

### Options

| Flag | Default | Description |
|---|---|---|
| `--deck, -d TEXT` | Input filename stem | Anki deck name |
| `--model, -m TEXT` | Config default | Model to use (e.g. `gemini-2.0-flash-lite`) |
| `--provider, -p TEXT` | Config default | Provider override (`gemini`, `openai`, `openrouter`, `ollama`) |
| `--api-key TEXT` | Config / env var | API key override for this run |
| `--format [apkg\|csv\|tsv]` | `apkg` | Output format |
| `--output, -o PATH` | Auto-named from deck | Output file path |
| `--batch-size INT` | Provider default | Cards requested per LLM call |
| `--force` | Off | Ignore manifest; reprocess all files |
| `--tags TEXT` | None | Comma-separated tags applied to every generated card |
| `--vision / --no-vision` | Model default | Override vision capability for this run |
| `--parsing-model TEXT` | Config default | Use a separate model for markitdown image OCR |
| `--prompt PATH` | Config default | Use a specific prompt file for this run |
| `--review` | Off | Launch browser review UI before exporting |
| `--dry-run` | Off | Print extracted text chunks to stdout; skip generation and export |
| `--instruct, -i TEXT` | None | Extra instructions surrounded by quotes, appended to the active prompt for this run |

### Examples

```bash
# Process all supported files in a folder
ankirai generate lectures/ --deck "BIOL 301"

# Reprocess everything, ignoring manifest
ankirai generate lectures/ --deck "BIOL 301" --force

# Single file, default output name
ankirai generate lecture01.pdf --deck "Biochem"

# Multiple files
ankirai generate lecture01.pdf lecture02.pdf --deck "Biochem"

# Use a specific model
ankirai generate notes.pdf --provider openai --model gpt-4o --deck "Misc"

# Export as CSV instead of .apkg
ankirai generate notes.pdf --format csv -o cards.csv

# Apply extra tags to all cards
ankirai generate notes.pdf --deck "Physics" --tags "physics,midterm"

# Use a local Ollama model (no vision)
ankirai generate notes.md --provider ollama --model llama3 --no-vision --deck "Notes"

# Use a cheap model for OCR, a stronger model for generation
ankirai generate handwritten.pdf --parsing-model gemini-3.1-flash-lite --model gemini-3.1-pro-preview

# Review cards in the browser before exporting
ankirai generate lecture01.pdf --deck "Biochem" --review
```

---

## `ankirai config`

### `ankirai config show`

Print the current config file with API keys redacted.

```bash
ankirai config show
```

### `ankirai config set <key> <value>`

Update a single config value using dot-notation keys.

```bash
ankirai config set providers.gemini.api_key AIza...
ankirai config set generation.batch_size_online 20
```

---

## `ankirai prompt`

### `ankirai prompt show`

Print the currently active prompt (global or local).

```bash
ankirai prompt show
```

### `ankirai prompt edit`

Open the global prompt file in `$EDITOR`.

```bash
ankirai prompt edit
```

### `ankirai prompt reset`

Restore the built-in default prompt, overwriting the global prompt file.

```bash
ankirai prompt reset
```

---

## Configuration Priority

For any setting, ankirai resolves the value in this order (highest to lowest):

1. CLI flag (e.g. `--api-key`, `--model`)
2. Environment variable (e.g. `GEMINI_API_KEY`, `ANKIRAI_MODEL`)
3. Per-project `.env` file
4. User config file (`config.toml`)
5. Built-in default

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `ANKIRAI_PROVIDER` | Default provider override |
| `ANKIRAI_MODEL` | Default model override |
| `ANKIRAI_PARSING_MODEL` | Parsing model override |
