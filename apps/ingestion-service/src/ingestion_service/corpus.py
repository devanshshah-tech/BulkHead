import hashlib
import io
import logging
from abc import ABC, abstractmethod

from .config import Settings

logger = logging.getLogger(__name__)


class CorpusVersioner(ABC):
    @abstractmethod
    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str: ...


class NullVersioner(CorpusVersioner):
    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str:
        # Fallback content-addressable hash when lakeFS is not enabled
        return hashlib.sha256(data).hexdigest()[:16]


class LakeFSVersioner(CorpusVersioner):
    def __init__(self, settings: Settings) -> None:
        import lakefs_sdk

        self._sdk = lakefs_sdk
        self._config = lakefs_sdk.Configuration(
            host=settings.lakefs_endpoint,
            username=settings.lakefs_access_key or None,
            password=settings.lakefs_secret_key or None,
        )
        self._client = lakefs_sdk.ApiClient(self._config)
        self._objects = lakefs_sdk.ObjectsApi(self._client)
        self._commits = lakefs_sdk.CommitsApi(self._client)
        self._repos = lakefs_sdk.RepositoriesApi(self._client)
        self._auth = lakefs_sdk.AuthApi(self._client)
        self._repo = settings.lakefs_repo
        self._branch = settings.lakefs_branch
        self._access_key = settings.lakefs_access_key
        self._secret_key = settings.lakefs_secret_key
        self._initialized = False

    def _ensure_repo(self) -> None:
        if self._initialized:
            return
        try:
            setup_state = self._auth.get_setup_state()
            uninit = getattr(setup_state, "state", None) == "not_initialized"
            if uninit and self._access_key and self._secret_key:
                try:
                    self._auth.setup(
                        self._sdk.Setup(
                            username="bulkhead",
                            key=self._sdk.AccessKeyCredentials(
                                access_key_id=self._access_key,
                                secret_access_key=self._secret_key,
                            ),
                        )
                    )
                except Exception as ex:
                    logger.warning("lakeFS setup call failed: %s", ex)

            try:
                self._repos.get_repository(self._repo)
            except Exception:
                try:
                    self._repos.create_repository(
                        self._sdk.RepositoryCreation(
                            name=self._repo,
                            storage_namespace=f"local:///data/blockstore/{self._repo}",
                            default_branch=self._branch,
                        )
                    )
                except Exception as repo_ex:
                    logger.warning("Failed to create repository '%s': %s", self._repo, repo_ex)
            self._initialized = True
        except Exception as ex:
            logger.warning("Could not auto-initialize lakeFS repository '%s': %s", self._repo, ex)

    def commit(self, key: str, data: bytes, metadata: dict[str, str]) -> str:
        fallback_hash = hashlib.sha256(data).hexdigest()[:16]
        try:
            self._ensure_repo()
            self._objects.upload_object(self._repo, self._branch, key, content=io.BytesIO(data))
            creation = self._sdk.CommitCreation(message=f"ingest {key}", metadata=metadata)
            commit = self._commits.commit(self._repo, self._branch, creation)
            return str(commit.id)
        except Exception as ex:
            logger.warning(
                "lakeFS commit failed for '%s' (%s); using content hash fallback", key, ex
            )
            return fallback_hash


def create_versioner(settings: Settings) -> CorpusVersioner:
    if settings.lakefs_enabled:
        return LakeFSVersioner(settings)
    return NullVersioner()
