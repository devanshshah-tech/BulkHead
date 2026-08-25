import pytest

from ingestion_service.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\t ") == []


def test_short_text_is_single_chunk():
    assert chunk_text("hello world", chunk_size=100, overlap=10) == ["hello world"]


def test_long_text_splits_with_overlap():
    words = [f"w{i:03d}" for i in range(100)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)
    assert all(c in text for c in chunks)
    for prev, nxt in zip(chunks, chunks[1:]):  # noqa: B905
        prev_words = set(prev.split())
        next_words = set(nxt.split())
        assert prev_words & next_words, "expected overlap between adjacent chunks"


def test_every_word_is_preserved():
    words = [f"w{i}" for i in range(50)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=30, overlap=6)
    assert set(" ".join(chunks).split()) == set(words)


def test_invalid_parameters_raise():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)
