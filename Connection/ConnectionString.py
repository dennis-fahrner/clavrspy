from re import compile

USER_AUTH = "@"


def __compile_pattern():
    # any_char = r"[a-zA-Z\d_.-]"
    # lifetime_re = r"/'[a-z]"
    # param = r"[^ &:]"
    param = r"[a-zA-Z\d_.-]"
    user_auth = USER_AUTH
    pattern = compile(f"^{param}+{user_auth}{param}+/[?]" +
                      f"({param}+:{param}+(?:&{param}+:{param}+)*)?$")
    return pattern


connection_regex = __compile_pattern()


class ConnectionString:
    __string: str
    user: str
    auth: str
    # Optional Arguments
    name: str
    test: int

    def __init__(self, connection_string: str):
        self.__string = connection_string
        # print(pattern.pattern)

        if not connection_regex.fullmatch(connection_string):
            raise ValueError(f"Invalid Connection String, string must conform to {connection_regex.pattern}")

        user_and_auth, connection_string = connection_string.split("/")

        self.user, self.auth = user_and_auth.split(USER_AUTH)

        if not connection_string.__contains__("?"):
            return

        # Skip the '?'
        connection_string = connection_string[1:]

        while connection_string != "":
            if connection_string.__contains__("&"):
                arg_and_value, connection_string = connection_string.split("&", maxsplit=1)
            else:
                arg_and_value = connection_string
                connection_string = ""

            arg, value = arg_and_value.split(":")

            if hasattr(self, arg):
                raise ValueError(f"Value {arg} already defined as {getattr(self, arg)}")

            if not self.__annotations__.__contains__(arg):
                raise ValueError(f"Value {arg} is not valid parameter")

            try:
                setattr(self, arg, self.__annotations__[arg](value))
            except (TypeError | ValueError):
                raise TypeError(f"Value {arg} has to be type {self.__annotations__[arg]} but is {type(arg)}")

    @property
    def string(self):
        return self.__string

    def __str__(self):
        repr_string = f"{self.user}:{self.auth}"
        # add values

        attributes = [k for k, v in self.__dict__.items()
                      if k not in {"user", "auth"}
                      and not k.startswith("_")
                      and hasattr(self, k)]

        if attributes:
            repr_string += " -> ["
            repr_string += " | ".join(
                [f"{attr}:{getattr(self, attr)}" for attr in attributes])
            repr_string += "]"
        return repr_string

    def __repr__(self):
        return str(self)
