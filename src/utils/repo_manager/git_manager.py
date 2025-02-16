import os
import shutil
from git import Repo # type: ignore

from src.settings import TMP_REPOS_DIR
from src.utils.repo_manager.dir_manager import DirManager


class GitManager(DirManager):
    __slots__ = ('path', 'delete_after_use')

    def __init__(self, url, delete_after_use: bool = True):
        self.delete_after_use = delete_after_use

        repo_name = self._get_repo_name(url)
        self.path = os.path.join(TMP_REPOS_DIR, repo_name)
        self.path = os.path.abspath(self.path)

        if not os.path.exists(TMP_REPOS_DIR):
            os.makedirs(TMP_REPOS_DIR)

        if not os.path.exists(self.path):
            Repo.clone_from(url, self.path)
        else:
            print(f"Репозиторий {repo_name} уже существует в {self.path}")


    def _get_repo_name(self, repo_url: str) -> str:
        return repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    

    def __del__(self):
        if self.delete_after_use and os.path.exists(self.path):
            shutil.rmtree(self.path)