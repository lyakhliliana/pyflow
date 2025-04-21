import os
import logging
from git import Repo, GitCommandError
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GitHandler:
    __slots__ = ('_repos')

    def __init__(self):
        self._repos: Dict[str, Path] = dict()

    @staticmethod
    def clone_repo(repo_url: str, destination: str = "", force_clone: bool = True) -> Optional[Path]:
        if destination == "":
            destination = os.getcwd()

        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)

        repo_name = GitHandler.extract_repo_name(repo_url)
        repo_path = dest_path / repo_name

        if repo_path.exists() and not force_clone:
            logger.info(f"Using cached repository at {repo_path}")
            return repo_path

        try:
            logger.info(f"Cloning repository {repo_url} to {repo_path}")
            Repo.clone_from(repo_url, repo_path, depth=1)
            return repo_path
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return None

    @staticmethod
    def extract_repo_name(repo_url: str) -> str:
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        return repo_url.split("/")[-1]

    @staticmethod
    def clean_repo(repo: str):
        repo_path = Path(repo)
        if not repo_path.exists():
            logger.info(f"{repo} does not exist.")
            return

        if repo_path.is_dir():
            logger.info(f"Removing {repo}")
            os.system(f"rm -rf {repo}")
