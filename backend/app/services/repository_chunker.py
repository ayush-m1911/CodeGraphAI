"""
Purpose:
Aggregates and chunks all Python files within a repository.

Role in CodeGraphAI:
Bridges file traversal (`parser.py`) and logical block extraction (`code_chunker.py`) by reading parsed documents,
filtering for Python files, running AST chunking, and compiling a unified list of logical chunks ready for vector embeddings.

Key Responsibilities:
* Collect loaded documents from repository parser.
* Filter for Python files (checking for `.py` extension).
* Run Tree-sitter AST chunking on each file.
* Compile and return a unified list of code chunks with metadata.
"""

from app.services.parser import (
    parse_repository
)

from app.services.code_chunker import (
    extract_python_chunks
)


def create_code_chunks(
    repo_path
):
    """
    Parses and chunks all Python files in the repository.

    Args:
        repo_path (str): Root path of the repository to process.

    Returns:
        list of dict: A combined list of AST code chunks from all Python files in the repository.
    """

    docs = parse_repository(
        repo_path
    )

    all_chunks = []

    for doc in docs:

        if not doc["file_path"].endswith(
            ".py"
        ):
            continue

        chunks = extract_python_chunks(
            doc["content"],
            doc["file_path"]
        )

        all_chunks.extend(chunks)

    return all_chunks