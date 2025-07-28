from __future__ import annotations

import ast
from typing import Any


def from_response(message: str, give_error: bool) -> Any:
    try:
        return ast.literal_eval(message)
    except Exception as e:
        if message == "Ok" or message == "+Queue":
            return True
        elif message.startswith("Err"):
            if give_error:
                raise Exception(message)
            else:
                return False
        else:
            return message
