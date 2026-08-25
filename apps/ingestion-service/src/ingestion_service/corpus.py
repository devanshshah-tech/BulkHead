import io
from abc import ABC, abstractmethod

from .config import Settings


class CorpusVersioner(ABC):
    @abstractmethod
    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str: ...


class NullVersioner(CorpusVersioner):
    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str:
        return ""


class LakeFSVersioner(CorpusVersioner):
    def __init__(self, settings: Settings) -> None:
        import lakefs.sdk
        from lakefs.sdk.client import ApiClient, Configuration

        config = Configuration(
            host=settings.lakefs_endpoint,
            username=settings.lakefs_access_key,
            password=settings.lakefs_secret_key,
        )
        client = ApiClient(config)
        self._objects = lakefs.sdk.ObjectsApi(client)
        self._commits = lakefs.sdk.CommitsApi(client)
        self._commit_model = lakefs.sdk.CommitCreation
        self._repo = settings.lakefs_repo
        self._branch = settings.lakefs_branch

    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str:
        self._objects.upload_object(self._repo, self._branch, key, content=io.BytesIO(data))
        creation = self._commit_model(message=f"ingest {key}", metadata=metadata)
        commit = self._commits.commit(self._repo, self._branch, creation)
        return str(commit.id)


def create_versioner(settings: Settings) -> CorpusVersioner:
    if settings.lakefs_enabled:
        return LakeFSVersioner(settings)
    return NullVersioner()
