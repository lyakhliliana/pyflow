import os
import logging
from git import Repo, GitCommandError
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TMP_REPO_DIR = "./tmp/repos"


class GitHandler:
    __slots__ = ('cache_dir')

    def __init__(self, cache_dir: str = TMP_REPO_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def clone_repo(self, repo_url: str, force_clone: bool = False) -> Optional[Path]:
        repo_name = self._extract_repo_name(repo_url)
        repo_path = self.cache_dir / repo_name

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

    def _extract_repo_name(self, repo_url: str) -> str:
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        return repo_url.split("/")[-1]

    def cleanup(self):
        for item in self.cache_dir.iterdir():
            if item.is_dir():
                logger.info(f"Removing {item}")
                os.system(f"rm -rf {item}")
