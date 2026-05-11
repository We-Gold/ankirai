from ankirai.parse import chunk_markdown


def test_chunk_by_headings():
    # Two small sections fit within max_chars so they are merged into one chunk
    text = "# Section 1\nContent A\n\n# Section 2\nContent B"
    chunks = chunk_markdown(text)
    assert len(chunks) == 1
    assert "Section 1" in chunks[0]
    assert "Section 2" in chunks[0]


def test_chunk_by_headings_splits_when_large():
    # Two large sections should stay as separate chunks
    big = "word " * 700  # ~3500 chars each
    text = f"# Section 1\n{big}\n\n# Section 2\n{big}"
    chunks = chunk_markdown(text, max_chars=3000)
    assert len(chunks) >= 2
    assert any("Section 1" in c for c in chunks)


def test_chunk_fallback_no_headings():
    text = "a" * 9000
    chunks = chunk_markdown(text, max_chars=3000)
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk) <= 3000


def test_chunk_merges_small_sections():
    # Two small sections should be merged into one chunk
    text = "# A\nshort\n\n# B\nalso short"
    chunks = chunk_markdown(text, max_chars=3000)
    assert len(chunks) == 1


def test_chunk_splits_when_over_limit():
    big_section = "# Big\n" + "x " * 2000  # ~4000 chars
    small_section = "# Small\nfew words"
    text = big_section + "\n\n" + small_section
    chunks = chunk_markdown(text, max_chars=3000)
    assert len(chunks) >= 2


def test_chunk_empty_input():
    assert chunk_markdown("") == []


def test_chunk_strips_whitespace():
    text = "\n\n# Title\n\nSome text\n\n"
    chunks = chunk_markdown(text)
    for chunk in chunks:
        assert chunk == chunk.strip()
