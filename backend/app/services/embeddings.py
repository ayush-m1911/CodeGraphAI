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

_embedding_model = None

def get_embedding_model():
    """
    Lazily loads the BAAI/bge-small-en-v1.5 transformer model on first inference,
    preventing server boot delays, memory exhaustion, and port binding timeouts during startup.
    """
    global _embedding_model
    if _embedding_model is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5"
        )
    return _embedding_model

class _LazyEmbeddingProxy:
    """Transparent proxy that forwards calls to the lazily-loaded embedding model."""
    def __getattr__(self, name):
        model = get_embedding_model()
        return getattr(model, name)

# Global singleton proxy preserving backward compatibility with all callers
embedding_model = _LazyEmbeddingProxy()