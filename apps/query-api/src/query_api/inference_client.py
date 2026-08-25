from typing import Protocol

import httpx

from .config import Settings


class InferenceClient(Protocol):
    @property
    def model(self) -> str: ...

    def generate(self, prompt: str) -> str: ...

    def healthy(self) -> bool: ...


class StubInference:
    """Deterministic stand-in so the platform runs without a model pulled."""

    @property
    def model(self) -> str:
        return "stub-grounded-0.1"

    def generate(self, prompt: str) -> str:
        return (
            "Answer generated from the provided context only. "
            "See citations for the supporting document chunks."
        )

    def healthy(self) -> bool:
        return True


class OllamaInference:
    def __init__(self, url: str, model: str, timeout_seconds: float) -> None:
        self._url = url.rstrip("/")
        self._model = model
        self._http = httpx.Client(timeout=timeout_seconds)

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str:
        resp = self._http.post(
            f"{self._url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return str(resp.json()["response"])

    def healthy(self) -> bool:
        try:
            resp = self._http.get(f"{self._url}/api/tags")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False


def create_inference(settings: Settings) -> InferenceClient:
    if settings.inference_backend == "ollama":
        return OllamaInference(
            settings.ollama_url, settings.ollama_model, settings.ollama_timeout_seconds
        )
    return StubInference()
