def is_version_number(element):
    text = element.text
    if len(text) == 0:
        raise ValueError, "Version number cannot be empty."
    for ch in text:
        if not (('0' <= ch <= '9') or (ch == '.')):
            raise ValueError, "Bad character in version number: %s"%(repr(ch))

