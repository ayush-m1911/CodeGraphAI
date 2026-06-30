"""
Purpose:
Traverses the repository directory structure to locate and read valid source code documents.

Role in CodeGraphAI:
Acts as the file discovery and loading stage. Instead of parsing binary or configuration files,
it filters files based on supported extensions (e.g., .py) and ignores common non-code directories
(e.g., .git, venv) to feed clean document contents into the chunking pipeline.

Key Responsibilities:
* Traverse the cloned repository directory recursively using os.walk.
* Prune search directories dynamically using a predefined IGNORED_DIRS set to optimize traversal time.
* Read supported source code documents (restricted to ALLOWED_EXTENSIONS) with UTF-8 encoding.
* Return a list of document objects containing file path metadata and raw string content.

Interview Readiness Note:
- Filtering directories like `.git`, `node_modules`, `venv`, and `tests` prevents search space pollution.
- Restricting files to key coding extensions avoids scanning massive build outputs or compiled bytecode.
"""

import os

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
}

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "docs",
    "docs_src",
    "tests"
}


def parse_repository(repo_path: str):
    """
    Traverses the directory path recursively to load valid source code files.

    Args:
        repo_path (str): Path to the cloned repository.

    Returns:
        list of dict: A list of documents, where each dict has keys "file_path" and "content".
    """

    documents = []

    for root, dirs, files in os.walk(repo_path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
        ]

        for file in files:

            extension = os.path.splitext(file)[1]

            if extension not in ALLOWED_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read()

                documents.append(
                    {
                        "file_path": file_path,
                        "content": content
                    }
                )

            except Exception:
                continue

    return documents