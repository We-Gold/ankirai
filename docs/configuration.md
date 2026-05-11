# Configuration

ankirai stores its configuration in a TOML file in the platform config directory:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/ankirai/config.toml` |
| Linux | `~/.config/ankirai/config.toml` |
| Windows | `%APPDATA%\ankirai\config.toml` |

The file is created by `ankirai init` and given owner-only permissions (`600`). You can edit it directly or use `ankirai config set`.

---

## Config file format

### `[providers]`

```toml
[providers]
default = "gemini"   # active provider
```

### `[providers.<name>]`

One section per provider you want to configure. Valid names: `gemini`, `openai`, `openrouter`, `ollama`.

```toml
[providers.gemini]
api_key      = "AIza..."           # API key (keep this secret)
default_model = "gemini-3.1-flash-lite"  # model override
base_url     = ""                  # custom endpoint (optional)
vision       = true                # enable vision capability
```

| Key | Type | Default | Description |
|---|---|---|---|
| `api_key` | string | `""` | Provider API key |
| `default_model` | string | Provider default | Model to use when `--model` is not passed |
| `base_url` | string | `""` | Custom API base URL (required for OpenRouter and Ollama) |
| `vision` | bool | `true` for online providers | Whether to pass images to the model |

### `[generation]`

```toml
[generation]
batch_size_online = 15    # cards per LLM request for online providers
batch_size_local  = 5     # cards per LLM request for Ollama
parsing_model     = ""    # separate model for image/PDF OCR (optional)
```

| Key | Type | Default | Description |
|---|---|---|---|
| `batch_size_online` | int | `15` | Request size for Gemini, OpenAI, OpenRouter |
| `batch_size_local` | int | `5` | Request size for Ollama |
| `parsing_model` | string | `""` | If set, used only for markitdown OCR; main model is used for card generation |

---

## Full examples

### Gemini (default setup from `ankirai init`)

```toml
[providers]
default = "gemini"

[providers.gemini]
api_key = "AIza..."
```

### OpenAI with a custom default model

```toml
[providers]
default = "openai"

[providers.openai]
api_key       = "sk-..."
default_model = "gpt-5.4-nano"
```

### Ollama (local, no API key)

```toml
[providers]
default = "ollama"

[providers.ollama]
base_url      = "http://localhost:11434"
default_model = "llama4"
vision        = false
```

### Claude / Anthropic models via OpenRouter

```toml
[providers]
default = "openrouter"

[providers.openrouter]
api_key       = "sk-or-..."
default_model = "anthropic/claude-haiku-4-5"
base_url      = "https://openrouter.ai/api/v1"
```

### Smaller batches to avoid rate limits

```toml
[generation]
batch_size_online = 8
```

### Cheap OCR model + strong generation model

```toml
[generation]
parsing_model = "gemini-3.1-flash-lite"

[providers.gemini]
api_key       = "AIza..."
default_model = "gemini-3.1-pro-preview"
```

---

## Environment variables

Settings can also be provided via environment variables or a `.env` file in the working directory. CLI flags always win over env vars, and env vars always win over `config.toml`.

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `ANKIRAI_PROVIDER` | Active provider override |
| `ANKIRAI_MODEL` | Model override |
| `ANKIRAI_PARSING_MODEL` | Parsing model override |

---

## Resolution order

For any setting, ankirai resolves the value in this order (first wins):

1. CLI flag (`--api-key`, `--model`, `--provider`, …)
2. Environment variable
3. `.env` file in the working directory
4. `config.toml`
5. Built-in default
