from __future__ import annotations


def correct_rust_fmt(string: str) -> str:
    # If no Some(, true or false is present this correction is not needed
    if not (string.__contains__("Some(") or string.__contains__("true") or string.__contains__("false")):
        return string

    in_quotes: bool = False
    buffer: str = ""
    swallow_bracket: bool = False

    # Iterate over the string
    for char in string:
        if char == '"':
            in_quotes = not in_quotes

        # Swallow the Some(...) closing brackets
        if char == ")" and swallow_bracket and not in_quotes:
            swallow_bracket = False
            # Swallow bracket and continue
            continue

        # If the last 5 characters are the opening to Some(...)
        # and we are not currently in quotes remove the 'Some(' and wait for the closing bracket
        if buffer.endswith("Some(") and not in_quotes:
            buffer = buffer[:-5]
            swallow_bracket = True

        # This section only applies to the exists command
        if buffer.endswith("true") and not in_quotes:
            buffer = buffer[:-4] + "T" + buffer[-3:]

        if buffer.endswith("false") and not in_quotes:
            buffer = buffer[:-5] + "F" + buffer[-4:]

        buffer += char
    return buffer
