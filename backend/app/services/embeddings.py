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

from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)