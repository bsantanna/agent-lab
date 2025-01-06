from abc import ABC, abstractmethod


class OpenSearchPort(ABC):
    @abstractmethod
    def set(self, index: str, data: dict, mapping: dict = None):
        pass

    @abstractmethod
    def get(self, index: str, body: dict):
        pass
