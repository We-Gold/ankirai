"""
CLI entrypoint — commands and flags only, no business logic.
"""

from __future__ import annotations

from pathlib import Path

import click

from .config import DEFAULT_PROMPT, config_path, load_config, prompt_path, run_init

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".txt",
    ".md",
    ".rtf",
    ".epub",
    ".html",
    ".htm",
    ".csv",
    ".xml",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".tiff",
}


@click.group()
def cli() -> None:
    """ankirai — transform your notes into Anki flashcards at lightning speed."""


@cli.command()
def init() -> None:
    """First-time setup: configure provider and API key."""
    run_init()


@cli.command()
@click.argument("inputs", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--deck", "-d", default=None, help="Anki deck name")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--provider", "-p", default=None, help="Provider override")
@click.option("--api-key", default=None, help="API key override")
@click.option(
    "--format", "output_format", default="apkg", type=click.Choice(["apkg", "csv", "tsv"])
)
@click.option("--output", "-o", default=None, type=click.Path(), help="Output file path")
@click.option("--batch-size", default=None, type=int, help="Cards per LLM request")
@click.option("--force", is_flag=True, help="Ignore manifest; reprocess all files")
@click.option("--tags", default=None, help="Comma-separated tags to apply to all cards")
@click.option("--vision/--no-vision", default=None, help="Override vision capability")
@click.option(
    "--parsing-model", default=None, help="Use a different model for markitdown image parsing"
)
@click.option(
    "--prompt",
    "prompt_file",
    default=None,
    type=click.Path(exists=True),
    help="Prompt file override",
)
@click.option("--review", is_flag=True, help="Launch browser review UI before export")
@click.option("--dry-run", is_flag=True, help="Print extracted text chunks; skip generation")
def generate(
    inputs: tuple[str, ...],
    deck: str | None,
    model: str | None,
    provider: str | None,
    api_key: str | None,
    output_format: str,
    output: str | None,
    batch_size: int | None,
    force: bool,
    tags: str | None,
    vision: bool | None,
    parsing_model: str | None,
    prompt_file: str | None,
    review: bool,
    dry_run: bool,
) -> None:
    """Parse input files and generate an Anki deck."""
    from . import manifest as manifest_mod
    from .export import write_apkg, write_csv
    from .generate import generate_cards
    from .parse import parse_file

    config = load_config(
        provider=provider,
        model=model,
        api_key=api_key,
        vision=vision,
        batch_size=batch_size,
        prompt_file=prompt_file,
        parsing_model=parsing_model,
    )

    extra_tags = [t.strip() for t in tags.split(",")] if tags else []

    deck_name = deck or Path(inputs[0]).stem

    # Expand directories; track which manifest each file belongs to.
    # Directory inputs → manifest lives inside that directory.
    # Bare file inputs → manifest lives in cwd.
    raw_paths: list[Path] = []
    file_to_manifest: dict[Path, Path] = {}
    for i in inputs:
        p = Path(i)
        if p.is_dir():
            manifest_p = (p / "ankirai_manifest.json").resolve()
            for f in sorted(p.rglob("*")):
                raw_paths.append(f)
                file_to_manifest[f.resolve()] = manifest_p
        else:
            manifest_p = Path("ankirai_manifest.json").resolve()
            raw_paths.append(p)
            file_to_manifest[p.resolve()] = manifest_p

    # Apply extension allowlist and prompt/manifest exclusion
    input_paths: list[Path] = []
    for f in raw_paths:
        if not f.is_file():
            continue
        if f.name in {"ankirai_prompt.md", "ankirai_manifest.json"}:
            continue
        if f.suffix.lower() not in SUPPORTED_EXTENSIONS:
            click.echo(f"  skipping unsupported file type: {f.name}", err=True)
            continue
        input_paths.append(f)

    # Load all relevant manifests
    manifests: dict[Path, dict] = {}
    for mp in set(file_to_manifest.values()):
        manifests[mp] = manifest_mod.load(mp)

    # Skip already-processed files (unless --force)
    if not force:
        skipped = [
            f
            for f in input_paths
            if manifest_mod.is_processed(manifests[file_to_manifest[f.resolve()]], f)
        ]
        input_paths = [
            f
            for f in input_paths
            if not manifest_mod.is_processed(manifests[file_to_manifest[f.resolve()]], f)
        ]
        if skipped:
            click.echo(
                f"  skipping {len(skipped)} already-processed file(s) (use --force to reprocess)"
            )

    if not input_paths:
        click.echo("No files to process.")
        return

    # Resolve output path
    if output:
        output_path = Path(output)
    else:
        suffix = {"apkg": ".apkg", "csv": ".csv", "tsv": ".tsv"}[output_format]
        output_path = Path(deck_name.replace(" ", "_") + suffix)

    # Parse — record each file into its manifest as we go
    all_chunks = []
    for path in input_paths:
        all_chunks.extend(parse_file(path, config))
        manifest_mod.record(manifests[file_to_manifest[path.resolve()]], path)

    if not all_chunks:
        click.echo("No content extracted from input files.", err=True)
        raise SystemExit(1)

    if dry_run:
        click.echo(f"\n--- {len(all_chunks)} chunk(s) extracted ---\n")
        for chunk in all_chunks:
            click.echo(f"[{chunk.source_file} · chunk {chunk.chunk_index}]")
            click.echo(chunk.text)
            click.echo()
        return

    # Generate
    all_cards = generate_cards(all_chunks, config)

    if extra_tags:
        for card in all_cards:
            card.tags = list(set(card.tags) | set(extra_tags))

    # Review (optional)
    if review:
        from .review.server import run_review_server

        all_cards = run_review_server(all_cards)
        click.echo(f"  Review complete. {len(all_cards)} cards accepted.")
        if not all_cards:
            click.echo("No cards accepted. Nothing to export.")
            return

    # Export
    if output_format == "apkg":
        write_apkg(all_cards, deck_name, output_path)
    elif output_format == "csv":
        write_csv(all_cards, output_path, delimiter=",")
    elif output_format == "tsv":
        write_csv(all_cards, output_path, delimiter="\t")

    # Persist all manifests only after successful export
    for mp, mdata in manifests.items():
        manifest_mod.save(mdata, mp)


@cli.group("config")
def config_group() -> None:
    """Manage ankirai configuration."""


@config_group.command("show")
def config_show() -> None:
    """Print current config with API keys redacted."""
    import re

    cfg = config_path()
    if not cfg.exists():
        click.echo("No config file found. Run 'ankirai init' first.")
        return
    text = cfg.read_text()
    # Redact values on lines containing api_key
    text = re.sub(r'(api_key\s*=\s*")[^"]*(")', r"\1***\2", text)
    click.echo(text)


@config_group.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Update a config value (e.g. 'openai.api_key sk-...')."""
    import tomllib

    import tomli_w  # type: ignore[import]

    cfg = config_path()
    if not cfg.exists():
        click.echo("No config file found. Run 'ankirai init' first.")
        return
    with open(cfg, "rb") as f:
        data = tomllib.load(f)
    parts = key.split(".")
    node = data
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    cfg.write_text(tomli_w.dumps(data))
    click.echo(f"Set {key} = {value!r}")


@cli.group("prompt")
def prompt_group() -> None:
    """Manage the card generation prompt."""


@prompt_group.command("show")
def prompt_show() -> None:
    """Print the currently active prompt."""
    p = prompt_path()
    if p.exists():
        click.echo(p.read_text())
    else:
        click.echo(DEFAULT_PROMPT)


@prompt_group.command("edit")
def prompt_edit() -> None:
    """Open the global prompt in $EDITOR."""
    import os
    import subprocess

    p = prompt_path()
    if not p.exists():
        p.write_text(DEFAULT_PROMPT)
    editor = os.environ.get("EDITOR", "vi")
    subprocess.call([editor, str(p)])


@prompt_group.command("reset")
def prompt_reset() -> None:
    """Restore the default built-in prompt."""
    prompt_path().write_text(DEFAULT_PROMPT)
    click.echo("Prompt reset to default.")
