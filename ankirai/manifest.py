import hashlib
import json
import time
from pathlib import Path


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load(manifest_path: Path) -> dict:
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {}


def save(manifest: dict, manifest_path: Path) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2))


def is_processed(manifest: dict, file_path: Path) -> bool:
    key = str(file_path.resolve())
    if key not in manifest:
        return False
    return manifest[key]["hash"] == file_hash(file_path)


def record(manifest: dict, file_path: Path) -> None:
    key = str(file_path.resolve())
    manifest[key] = {"hash": file_hash(file_path), "mtime": time.time()}
