def str2bytes(data: str) -> bytes:
    if isinstance(data, str):
        try:
            return bytes(map(ord, data))
        except ValueError:
            return data.encode('utf-8')
    elif isinstance(data, bytes):
        return data
    else:
        raise ValueError("{} given ('str' expected)".format(type(data)))
