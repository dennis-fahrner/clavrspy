from __future__ import annotations

from typing import Union, List

from Connection.DataPointer import DataPointer


def fmt(data: Union[DataPointer, List[DataPointer], str, List[str]]):
    if isinstance(data, DataPointer):
        return f'"{data.id}"'
    elif isinstance(data, str):
        return f'"{data}"'
    elif isinstance(data, list):
        return "(" + ", ".join([fmt(d) for d in data]) + ")"
    else:
        raise NotImplementedError(f"fmt is not implemented for type {type(data)}")
