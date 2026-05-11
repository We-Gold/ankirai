import json
import time

from ankirai.manifest import file_hash, is_processed, load, record, save


def test_file_hash_is_deterministic(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hello")
    assert file_hash(f) == file_hash(f)


def test_file_hash_changes_with_content(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hello")
    h1 = file_hash(f)
    f.write_text("world")
    h2 = file_hash(f)
    assert h1 != h2


def test_load_returns_empty_dict_if_no_file(tmp_path):
    assert load(tmp_path / "missing.json") == {}


def test_load_reads_existing_manifest(tmp_path):
    mp = tmp_path / "manifest.json"
    mp.write_text(json.dumps({"key": "value"}))
    assert load(mp) == {"key": "value"}


def test_save_and_load_roundtrip(tmp_path):
    mp = tmp_path / "manifest.json"
    data = {"foo": {"hash": "abc", "mtime": 1.0}}
    save(data, mp)
    assert load(mp) == data


def test_record_stores_hash_and_mtime(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("content")
    manifest = {}
    before = time.time()
    record(manifest, f)
    after = time.time()
    key = str(f.resolve())
    assert key in manifest
    assert manifest[key]["hash"] == file_hash(f)
    assert before <= manifest[key]["mtime"] <= after


def test_is_processed_false_for_unknown_file(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hi")
    assert not is_processed({}, f)


def test_is_processed_true_after_record(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("hi")
    manifest = {}
    record(manifest, f)
    assert is_processed(manifest, f)


def test_is_processed_false_after_content_change(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("original")
    manifest = {}
    record(manifest, f)
    f.write_text("changed")
    assert not is_processed(manifest, f)
