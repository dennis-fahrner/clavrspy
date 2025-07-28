from typing import Dict
from Connection.DataPointer import DataPointer


class Collection(object):
    __pointers: Dict[str, DataPointer] = {}

    def __init__(self):
        self.__pointers = dict()

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def get_new_pointer(self):
        # Return new, unsaved / unnamed DataPointer
        return DataPointer()

    def __getattr__(self, name) -> DataPointer:
        if name in Collection.__dict__:
            return object.__getattribute__(self, name)

        # Create the data if it does not exist
        if not self.__pointers.__contains__(name):
            self.__pointers[name] = DataPointer()
        return self.__pointers[name]
