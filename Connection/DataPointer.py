class DataPointer:
    __id: int
    __type: type = str

    @property
    def __class__(self):
        return self.__type

    @property
    def id(self):
        return self.__id

    def __init__(self):
        # Add the type check
        self.__id = id(self)
