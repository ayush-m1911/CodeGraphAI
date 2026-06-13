import os
import re
import shutil
import stat
import subprocess

def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree to handle read-only file permissions on Windows.
    This fixes permission errors when deleting Git pack files.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def validate_github_url(url: str) -> bool:
    """
    Validates if a URL is a public GitHub repository link.
    """
    pattern = r"^https?://(www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$"
    return bool(re.match(pattern, url.strip()))

def clone_repository(repo_url: str) -> str:
    """
    Clones a GitHub repository dynamically into repositories/current_repo.
    """
    # 1. Validate the GitHub URL
    if not validate_github_url(repo_url):
        raise ValueError(f"Invalid GitHub URL: '{repo_url}'. Currently supports GitHub repository URLs only.")

    repo_url = repo_url.strip()
    target_path = os.path.join("repositories", "current_repo")

    # 2. Ensure parent directory exists
    os.makedirs("repositories", exist_ok=True)

    # 3. Clean up existing repository path if it exists
    if os.path.exists(target_path):
        print(f"Removing existing directory at {target_path}...")
        try:
            shutil.rmtree(target_path, onerror=on_rm_error)
        except Exception as e:
            raise RuntimeError(f"Could not remove existing repository directory {target_path}: {str(e)}")

    # 4. Clone repo using subprocess
    print(f"Cloning repository {repo_url} into {target_path}...")
    try:
        subprocess.run(
            ["git", "clone", repo_url, target_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return target_path
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr or e.stdout or ""
        raise RuntimeError(f"Git clone failed. Details: {stderr_msg.strip()}")
    except FileNotFoundError:
        raise RuntimeError("Git CLI is not installed or not available in the system PATH.")
    except Exception as e:
        raise RuntimeError(f"Failed to clone repository: {str(e)}")