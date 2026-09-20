"""
Purpose:
Instantiates the sentence embedding model used for generating vector representations of code chunks.

Role in CodeGraphAI:
Provides a semantic translation layer, converting raw AST code block text into 384-dimensional dense vectors using the HuggingFace BAAI/bge-small-en-v1.5 model.

Key Responsibilities:
* Initialize the LangChain HuggingFace embeddings wrapper.
* Load and cache the BAAI/bge-small-en-v1.5 transformer model locally.

Interview Readiness Note:
- Why BAAI/bge-small-en-v1.5? BGE-small is a highly optimized, state-of-the-art embedding model with a compact 384-dimensional output.
  It computes embeddings extremely quickly locally, making it ideal for self-contained desktop search engines without requiring external cloud embeddings APIs.
"""

from typing import List

_embedding_model = None


class FastEmbedWrapper:
    """
    High-performance, ultra-lightweight embedding wrapper powered by FastEmbed (ONNX Runtime).
    Consumes only ~30MB RAM compared to 400MB+ for PyTorch, while producing 100% compatible
    384-dimensional dense vectors with BAAI/bge-small-en-v1.5.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)

    def embed_query(self, text: str) -> List[float]:
        """Generates a 384-dim embedding vector for a single query."""
        generator = self._model.embed([text])
        return next(generator).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates 384-dim embedding vectors for a batch of documents."""
        if not texts:
            return []
        generator = self._model.embed(texts)
        return [vec.tolist() for vec in generator]


def get_embedding_model():
    """
    Lazily initializes the FastEmbed model singleton on first inference.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = FastEmbedWrapper(model_name="BAAI/bge-small-en-v1.5")
    return _embedding_model


class _LazyEmbeddingProxy:
    """Transparent proxy that forwards calls to the lazily-loaded embedding model."""
    def __getattr__(self, name):
        model = get_embedding_model()
        return getattr(model, name)


# Global singleton proxy preserving backward compatibility with all callers
embedding_model = _LazyEmbeddingProxy()