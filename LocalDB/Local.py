from subprocess import Popen, PIPE #, DEVNULL
from typing import Any
from enum import Enum
import time
import sys

from LocalDB.get_path import get_path
from test.test_env import TEST_IP, TEST_PORT

RETRY_COUNT = 3


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
        if "linux" in self.path:        
            import subprocess
            proc=subprocess.Popen(['ls','-l'])  # <-- Change the command here
            proc.communicate()
        # https://stackoverflow.com/questions/14735001/ignoring-output-from-subprocess-popen
        address = ip + ":" + str(port)
        arguments = [str(self.path), "--address", address, "--mode", mode.value]
        # print(arguments)
        self.__process = Popen(arguments, stdout=sys.stdout, stderr=sys.stderr)
        self.__alive = True

        # Check if the launch was successful
        for _ in range(RETRY_COUNT):
            if _is_port_in_use(port):
                break
            time.sleep(0.5)
        else:
            raise ConnectionError(f"Database did not start up correctly or in time. {self.dead_dump()}")

    @classmethod
    def test_instance(cls):
        return Local(ip=TEST_IP, port=TEST_PORT, mode=Mode.Test)

    def dead_dump(self) -> str:
        # Check if process exited early
        if self.__process.poll() is not None:  # Process has exited
            stdout, stderr = self.__process.communicate()
            return f"Exited with ({self.__process.returncode}) STDOUT: {stdout.decode()}, STDERR: {stderr.decode()}"
        return ""

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
