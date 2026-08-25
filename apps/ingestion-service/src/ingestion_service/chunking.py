def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        added = len(word) + (1 if current else 0)
        if current and current_len + added > chunk_size:
            chunks.append(" ".join(current))
            keep: list[str] = []
            keep_len = 0
            for w in reversed(current):
                wlen = len(w) + (1 if keep else 0)
                if keep_len + wlen > overlap:
                    break
                keep.insert(0, w)
                keep_len += wlen
            current = keep
            current_len = keep_len
        current.append(word)
        current_len += added

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]
