import math

from ingestion_service.embeddings import HashEmbedder


def test_hash_embedder_is_deterministic():
    emb = HashEmbedder(dim=64)
    assert emb.embed(["hello world"]) == emb.embed(["hello world"])


def test_hash_embedder_outputs_are_normalized():
    emb = HashEmbedder(dim=64)
    [vec] = emb.embed(["some text here"])
    assert len(vec) == 64
    assert math.isclose(sum(v * v for v in vec), 1.0, rel_tol=1e-9)


def test_hash_embedder_empty_string():
    emb = HashEmbedder(dim=8)
    [vec] = emb.embed([""])
    assert vec == [0.0] * 8


def test_similar_texts_are_closer_than_unrelated():
    emb = HashEmbedder(dim=256)

    def cos(a, b):
        return sum(x * y for x, y in zip(a, b, strict=True))

    [a] = emb.embed(["the ship sailed through the storm"])
    [b] = emb.embed(["the ship sailed through the heavy storm"])
    [c] = emb.embed(["quarterly earnings grew substantially"])
    assert cos(a, b) > cos(a, c)
