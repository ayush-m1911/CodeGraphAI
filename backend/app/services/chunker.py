from langchain_text_splitters import RecursiveCharacterTextSplitter

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