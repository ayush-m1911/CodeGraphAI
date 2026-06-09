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