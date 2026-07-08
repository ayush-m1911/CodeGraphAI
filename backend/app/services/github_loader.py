"""
Purpose:
Manages downloading, cleaning, and validating GitHub repositories dynamically.

Responsibilities:
* Validate GitHub URL strings using regular expressions.
* Clone remote GitHub repositories dynamically using Git CLI subprocess calls.
* Handle file cleanups and directory replacements safely.
* Overcome Windows OS read-only permission issues when deleting Git pack files using a chmod hook.

Interaction with other modules:
* Driven by `indexing_service.py` to fetch source code bases for ingestion.

How it contributes to the production architecture:
Decouples workspace paths from hardcoded values. By accepting a dynamic `target_path`, the service supports
indexing multiple codebases concurrently without overwriting files, enabling multi-user and multi-tenant scaling.
"""

import logging
import os
import re
import shutil
import stat
import subprocess

logger = logging.getLogger("codegraphai.github_loader")


def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree to handle read-only file permissions on Windows.
    This dynamically updates permission flags to make files writeable before retrying deletion.

    Parameters:
        func (function): Callback function.
        path (str): File/dir path where error occurred.
        exc_info (tuple): Exception information.

    Returns:
        None

    Execution Flow:
        1. Modify path permissions to writeable.
        2. Re-run the deletion callback.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def validate_github_url(url: str) -> bool:
    """
    Checks if a URL matches public GitHub repository conventions.

    Parameters:
        url (str): Repository URL.

    Returns:
        bool: True if the pattern matches a public GitHub project link, False otherwise.

    Execution Flow:
        1. Apply regex matching standard GitHub URL patterns.
        2. Return evaluation boolean.
    """
    pattern = r"^https?://(www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$"
    return bool(re.match(pattern, url.strip()))


def clone_repository(repo_url: str, target_path: str = None) -> str:
    """
    Clones a GitHub repository dynamically into a target workspace directory.

    Parameters:
        repo_url (str): Public GitHub repository URL.
        target_path (str, optional): Target directory path. Defaults to "repositories/current_repo".

    Returns:
        str: Directory path where the repository was cloned.

    Execution Flow:
        1. Validate repository URL format.
        2. Set target path directory (default to repositories/current_repo if None).
        3. Clear existing directories at target path if they exist (handling Windows permissions).
        4. Spawn Git clone process using subprocess.
        5. Return path to cloned repo.
    """
    # 1. Validate the GitHub URL
    if not validate_github_url(repo_url):
        logger.error(f"Validation failed for URL: '{repo_url}'")
        raise ValueError(f"Invalid GitHub URL: '{repo_url}'. Currently supports GitHub repository URLs only.")

    repo_url = repo_url.strip()
    if not target_path:
        target_path = os.path.join("repositories", "current_repo")

    # 2. Ensure parent directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # 3. Clean up existing repository path if it exists
    if os.path.exists(target_path):
        logger.info(f"Removing existing directory at {target_path}...")
        try:
            shutil.rmtree(target_path, onerror=on_rm_error)
        except Exception as e:
            logger.warning(f"shutil.rmtree failed for {target_path}: {e}. Retrying with aggressive shell rmdir...")
            try:
                # Resolve to absolute path and execute cmd rmdir
                abs_target = os.path.abspath(target_path)
                subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", abs_target], check=True)
                logger.info(f"Successfully cleaned target directory aggressively: {target_path}")
            except Exception as shell_err:
                logger.error(f"Aggressive shell rmdir failed: {shell_err}")
                raise RuntimeError(f"Could not remove existing repository directory {target_path}: {str(e)}")


    # 4. Clone repo using subprocess
    logger.info(f"Cloning repository {repo_url} into {target_path}...")
    try:
        subprocess.run(
            ["git", "clone", repo_url, target_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        logger.info(f"Successfully cloned {repo_url} to {target_path}")
        return target_path
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr or e.stdout or ""
        logger.error(f"Git clone failed: {stderr_msg.strip()}")
        raise RuntimeError(f"Git clone failed. Details: {stderr_msg.strip()}")
    except FileNotFoundError:
        logger.error("Git CLI is not installed or not available in the system PATH.")
        raise RuntimeError("Git CLI is not installed or not available in the system PATH.")
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        raise RuntimeError(f"Failed to clone repository: {str(e)}")