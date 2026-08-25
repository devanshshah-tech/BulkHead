from typing import Protocol

from .config import Settings


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbedder:
    """Deterministic bag-of-bytes embedder for tests and offline dev."""

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self._dim
            for i, b in enumerate(text.encode("utf-8")):
                vec[(i * 31 + b) % self._dim] += 1.0
            norm = sum(v * v for v in vec) ** 0.5
            out.append([v / norm for v in vec] if norm else vec)
        return out


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        if hasattr(self._model, "get_embedding_dimension"):
            self._dim = int(self._model.get_embedding_dimension())
        else:
            self._dim = int(self._model.get_sentence_embedding_dimension())

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        embs = self._model.encode(texts, normalize_embeddings=True)
        return [row.tolist() for row in embs]


def create_embedder(settings: Settings) -> Embedder:
    if settings.embedder_backend == "hash":
        return HashEmbedder()
    return SentenceTransformerEmbedder(settings.embedding_model)
