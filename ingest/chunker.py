CHUNK_SIZE_WORDS = 400
CHUNK_OVERLAP_WORDS = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    n = len(words)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(" ".join(words[start:end]))
        if end == n:
            break
        start = max(end - overlap, start + 1)
    return chunks