from typing import List, Dict, Any


class RecursiveCharacterTextSplitter:
    """
    Lightweight recursive character text splitter implemented in pure Python
    with zero external framework dependencies.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, length_function=len):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        text_len = self.length_function(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunks.append(text[start:end])
            if end == text_len:
                break
            start += max(1, self.chunk_size - self.chunk_overlap)
        return chunks


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
)


def create_chunks(documents):

    chunks = []

    for doc in documents:

        splits = text_splitter.split_text(
            doc["content"]
        )

        for idx, chunk in enumerate(splits):

            chunks.append(
                {
                    "text": chunk,
                    "metadata": {
                        "file_path": doc["file_path"],
                        "chunk_id": idx
                    }
                }
            )

    return chunks