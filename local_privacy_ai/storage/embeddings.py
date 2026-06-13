from __future__ import annotations

import hashlib
from typing import Protocol


class EmbeddingModel(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


class HashingEmbedder:
    """Deterministic lightweight embedder for tests and offline smoke checks."""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in text.lower().split():
                digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
                index = int(digest, 16) % self.dimensions
                vector[index] += 1.0
            norm = sum(value * value for value in vector) ** 0.5 or 1.0
            vectors.append([value / norm for value in vector])
        return vectors
