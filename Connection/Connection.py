from __future__ import annotations
from typing import Dict, Optional, Union, List
import functools

from Connection.DBSocket.DBSocket import DBSocket
from Connection.DBSocket.TCPSocket import TCPSocket
from Connection.DataPointer import DataPointer
from Connection.ConnectionString import ConnectionString
from Connection.Collection import Collection
from typeguard import typechecked

from Connection._correct_rust_fmt import correct_rust_fmt
from Connection._fmt import fmt
from Connection._from_response import from_response


class User:
    user: str

    def __init__(self) -> None:
        self.user = ""


def __testhint__(op_type: str, restricted: bool = False):
    # Add any testhints that are necessary to differentiate functions here
    # e.g. if a method is read or write or if its restricted
    def decorator(func):
        func.__testhint__ = {"op_type": op_type}  # store metadata on original function
        if restricted:
            func.__testhint__["restricted"] = True
        @functools.wraps(func)
        def wrapper(*w_args, **w_kwargs):
            return func(*w_args, **w_kwargs)
        wrapper.__testhint__ = func.__testhint__  # type: ignore # copy to wrapper too
        return wrapper
    return decorator


@typechecked
class Connection:
    __pointers: Dict[str, DataPointer]
    __address: str
    __port: int
    __socket: DBSocket
    __frozen = False
    __user: User = User()

    def __init__(self, connection_string: str = "", socket: Optional[DBSocket] = None):
        self.__pointers = dict()

        if connection_string:
            try:
                connection_string_obj = ConnectionString(connection_string)
            except (ValueError, TypeError) as e:
                raise e
            # raise NotImplementedError

        self.__socket = socket or TCPSocket()
        self.__socket.connect()

        # Freeze this class
        self.__frozen = True

    def __setattr__(self, key, value):
        # https://stackoverflow.com/questions/3603502/prevent-creating-new-attributes-outside-init
        if self.__frozen:
            raise ValueError("%r does not support item assignment" % self)
        object.__setattr__(self, key, value)

    def __del__(self):
        self.close()

    def __delattr__(self, item):
        del self.__pointers[item]

    def __enter__(self) -> Connection:
        # Enters
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

        if exc_type is Exception:
            return False

        del self
        # Exits
        # closes connection

    @property
    def __alive__(self) -> bool:
        return self.__socket.__alive__

    @property
    def user(self) -> str:
        return self.__user.user

    def close(self):
        self.__socket.close()

    def _send_recv(self, msg: str, give_error: bool = True):
        self.__socket.send(msg)
        recv = self.__socket.recv()

        # Correct Some(...) (Rust Enum Type found in Get Return) if necessary
        recv = correct_rust_fmt(recv)

        return from_response(recv, give_error)

    def get_collection(self):
        return Collection()

    # Raw
    def raw(self, raw: str, give_error: bool = True):
        """
        Sends the raw string to the database
        >>> response = self.raw("Test")
        :param give_error: if true returns an error string instead of false
        :param raw: Raw string being sent
        :return: Return response to raw request
        """
        return self._send_recv(raw, give_error)

    # Read
    @__testhint__('read')
    def get(self, data: Union[DataPointer, List[DataPointer]]) -> List[List[str]]:
        """
        get returns the data stored at the location of each DataPointer.c
        If the Data Pointer is empty, returns an empty List
        :param data: DataPointer or List of DataPointers
        :return:
        """
        if isinstance(data, DataPointer):
            data = [data]

        return self._send_recv(f'GET {fmt(data)}')

    @__testhint__('read')
    def exists(self, data: Union[DataPointer, List[DataPointer]]) -> List[bool]:
        """
        exists returns whether a key is found in the database for each DataPointer.
        :param data: DataPointer or List of DataPointers
        :return:
        """
        if isinstance(data, DataPointer):
            data = [data]
        return self._send_recv(f'EXISTS {fmt(data)}')

    @__testhint__('read')
    def has(self, data: Union[DataPointer, List[DataPointer]], value: str) -> List[bool]:
        """
        has returns whether a keyword is present for one or more given pointers
        :param data: DataPointer or List of DataPointers
        :param value: value for which is checked in the Pointer(s)
        :return: Returns a list of booleans where each index is True if the corresponding pointer has the element,
         else it is False
        """
        if isinstance(data, DataPointer):
            data = [data]
        return self._send_recv(f'HAS {fmt(data)} {fmt(value)}')

    # Write
    @__testhint__('write')
    def put(self, data: Union[DataPointer, List[DataPointer]],
            value: Union[str, List[str], List[List[str]]]) -> bool:
        """
        :param data:
        :param value:
        :return:
        """
        # str
        if isinstance(value, str):
            value = [[value]]
        # List[str]
        elif isinstance(value, list):
            if value and not isinstance(value[0], list):
                value = [value] # type: ignore
        # DataPointer
        if isinstance(data, DataPointer):
            data = [data]

        return self._send_recv(f'PUT {fmt(data)} {fmt(value)}') # type: ignore

    @__testhint__('write')
    def delete(self, data: Union[DataPointer, List[DataPointer]]) -> bool:
        if isinstance(data, DataPointer):
            data = [data]

        return self._send_recv(f'DELETE {fmt(data)}')

    @__testhint__('write')
    def clear(self, data: Union[DataPointer, List[DataPointer]]) -> bool:
        if isinstance(data, DataPointer):
            data = [data]

        return self._send_recv(f'CLEAR {fmt(data)}')

    @__testhint__('write')
    def retract(self, data: Union[DataPointer, List[DataPointer]], value: Union[str, List[str]]) -> bool:
        # str
        if isinstance(value, str):
            value = [value]
        # DataPointer
        if isinstance(data, DataPointer):
            data = [data]

        return self._send_recv(f'RETRACT {fmt(data)} {fmt(value)}')

    @__testhint__('write')
    def replace(self, data: DataPointer, value: Union[str, List[str]]) -> bool:
        if isinstance(value, str):
            value = [value]

        return self._send_recv(f'REPLACE {fmt(data)} {fmt(value)}')

    # Restricted Write
    @__testhint__('write', restricted=False)
    def purge(self):
        return self._send_recv(f'PURGE')

    # Read-Write
    @__testhint__('write')
    def pop(self, data: DataPointer) -> List[str]:
        return self._send_recv(f'POP {fmt(data)}')

    # Transaction
    def start_transaction(self):
        return self._send_recv(f'SEQUENCE')

    def abort_transaction(self):
        return self._send_recv(f'ABORT')

    def execute_transaction(self):
        return self._send_recv(f'EXECUTE')
    
    # Authentication
    def authenticate(self, name, authtoken):
        recv: str = self._send_recv(f'AUTH {fmt(name)} {fmt(authtoken)}')
        
        # 3.8 version compatability
        try:
            self.__user.user = recv.removeprefix("Authenticated: ")
        except AttributeError:
            prefix = "Authenticated: "
            if recv.startswith(prefix):
                self.__user.user = recv[len(prefix):]
        return recv


class Transaction:
    connection: Connection
    __aborted: bool

    def __init__(self, connection: Connection):
        self.connection = connection
        self.__aborted: bool = False

    def abort(self):
        self.connection.abort_transaction()
        self.__aborted = True

    def __enter__(self) -> Transaction:
        self.connection.start_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Catch error if
        # On Exception abort transaction
        if exc_type is not None and issubclass(exc_type, Exception):
            if not self.__aborted:
                self.connection.abort_transaction()
            return False

        if not self.__aborted:
            self.connection.execute_transaction()
