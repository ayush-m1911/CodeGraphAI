from app.services.parser import (
    parse_repository
)

from app.services.code_chunker import (
    extract_python_chunks
)


def create_code_chunks(
    repo_path
):

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