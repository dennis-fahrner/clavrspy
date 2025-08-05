from abc import ABC, abstractmethod
from typeguard import typechecked
from typing import Optional

from Connection.ConnectionString import ConnectionString


class DBSocket(ABC):
    SEND_CHAR = ""
    ENCODING = "utf-8"
    BUFF_SIZE = 4096  # 4 KiB

    @property
    @abstractmethod
    def __alive__(self) -> bool:
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    @typechecked
    def send(self, msg: str):
        pass

    @abstractmethod
    def recv(self) -> str:
        pass

    @abstractmethod
    def close(self):
        pass
