import os
from src.utils.repo_manager.base_manager import BaseManager


class DirManager(BaseManager):
    __slots__ = ('path')

    def __init__(self, path):
        self.path = path
