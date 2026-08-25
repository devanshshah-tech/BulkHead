from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RetrieveRequest(_message.Message):
    __slots__ = ("query", "top_k", "corpus_ref")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    CORPUS_REF_FIELD_NUMBER: _ClassVar[int]
    query: str
    top_k: int
    corpus_ref: str
    def __init__(self, query: _Optional[str] = ..., top_k: _Optional[int] = ..., corpus_ref: _Optional[str] = ...) -> None: ...

class Chunk(_message.Message):
    __slots__ = ("chunk_id", "doc_id", "source", "content", "score", "corpus_commit", "ingested_at_unix")
    CHUNK_ID_FIELD_NUMBER: _ClassVar[int]
    DOC_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    CORPUS_COMMIT_FIELD_NUMBER: _ClassVar[int]
    INGESTED_AT_UNIX_FIELD_NUMBER: _ClassVar[int]
    chunk_id: str
    doc_id: str
    source: str
    content: str
    score: float
    corpus_commit: str
    ingested_at_unix: int
    def __init__(self, chunk_id: _Optional[str] = ..., doc_id: _Optional[str] = ..., source: _Optional[str] = ..., content: _Optional[str] = ..., score: _Optional[float] = ..., corpus_commit: _Optional[str] = ..., ingested_at_unix: _Optional[int] = ...) -> None: ...

class RetrieveResponse(_message.Message):
    __slots__ = ("chunks",)
    CHUNKS_FIELD_NUMBER: _ClassVar[int]
    chunks: _containers.RepeatedCompositeFieldContainer[Chunk]
    def __init__(self, chunks: _Optional[_Iterable[_Union[Chunk, _Mapping]]] = ...) -> None: ...

class HealthzRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthzResponse(_message.Message):
    __slots__ = ("database_ok",)
    DATABASE_OK_FIELD_NUMBER: _ClassVar[int]
    database_ok: bool
    def __init__(self, database_ok: _Optional[bool] = ...) -> None: ...
