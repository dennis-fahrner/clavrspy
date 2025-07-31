from subprocess import Popen, PIPE, DEVNULL
from typing import Any
from enum import Enum
import time
import sys

from LocalDB.get_path import get_path
from test.test_env import TEST_IP, TEST_PORT

RETRY_COUNT = 4


def _is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


class Mode(Enum):
    Test = "test"
    Default = "default"


class Local:
    path: str = get_path()
    __process: Popen
    # Is set to True once the process started running
    __alive: bool = False

    def __init__(
        self,
        ip: str = "127.0.0.1",
        port: int = 3254,
        _std_out: Any = PIPE,
        mode: Mode = Mode.Default,
        **_kwargs
    ):
        # https://stackoverflow.com/questions/14735001/ignoring-output-from-subprocess-popen
        address = ip + ":" + str(port)
        arguments = [str(self.path), "--address", address, "--mode", mode.value]
        
        # TODO, capture / save error outputs maybe with PIPE
        self.__process = Popen(arguments, stdout=DEVNULL, stderr=DEVNULL)
        self.__alive = True

        # Check if the launch was successful
        for i in range(RETRY_COUNT):
            if _is_port_in_use(port):
                break
            # Increasing timeout 0.5 -> 1.0 -> 2.0 -> 4.0
            time.sleep(0.5 * (2 ** i))
        else:
            raise ConnectionError("Database did not start up correctly or in time.")

    @classmethod
    def test_instance(cls):
        return Local(ip=TEST_IP, port=TEST_PORT, mode=Mode.Test)

    def kill(self):
        if self.__alive:
            self.__process.kill()
            # https://stackoverflow.com/questions/52476265/killing-shell-true-process-results-in-resourcewarning-subprocess-is-still-running
            self.__process.wait(timeout=0.5)

    def __del__(self):
        if self.__alive:
            # Kill db once its finished
            self.kill()
            self.__process.terminate()

def get_clavrs_version() -> str:
    process = Popen([str(get_path()), "--version"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate(timeout=5)
    if process.returncode != 0:
        raise RuntimeError(f"Failed to get version: {stderr.decode().strip()}")
    return stdout.decode().strip()
