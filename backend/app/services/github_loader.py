from git import Repo
import os
import shutil

REPO_ROOT = "repositories"


def clone_repository(repo_url: str):

    repo_name = repo_url.rstrip("/").split("/")[-1]

    local_path = os.path.join(REPO_ROOT, repo_name)

    if os.path.exists(local_path):
        shutil.rmtree(local_path)

    Repo.clone_from(repo_url, local_path)

    return {
        "repo_name": repo_name,
        "local_path": local_path
    }