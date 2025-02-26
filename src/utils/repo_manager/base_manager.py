from abc import ABC, abstractmethod


class BaseManager(ABC):
    __slots__ = ('path')

    @abstractmethod
    def __init__(self):
        pass
