from fastapi import APIRouter

from app.services.parser import parse_repository

router = APIRouter()


@router.get("/parse")
def parse():
    docs = parse_repository(
        "repositories/fastapi"
    )

    return {
        "total_files": len(docs),
        "sample": [
            {
                "file_path": doc["file_path"],
                "chars": len(doc["content"])
            }
            for doc in docs[:10]
        ]
    }


@router.get("/file/content")
def get_file_content(file_path: str):
    """
    Reads the content of a file from the ingested repository folder.
    """
    import os
    # Normalize path and check locations
    norm_path = os.path.normpath(file_path)
    
    # Try different search scopes
    paths_to_try = [
        norm_path,
        os.path.join("repositories/current_repo", norm_path),
        os.path.join("repositories", norm_path)
    ]
    
    for path in paths_to_try:
        if os.path.exists(path) and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return {
                    "success": True,
                    "file_path": path,
                    "content": content
                }
            except Exception as e:
                return {"success": False, "error": str(e), "content": ""}
                
    return {
        "success": False,
        "error": f"File not found at paths: {paths_to_try}",
        "content": ""
    }