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

def bytes2str(data: bytes) -> str:
    if isinstance(data, bytes):
        return ''.join(list(map(chr, data)))
    elif isinstance(data, str):
        return data
    else:
        raise ValueError("{} given ('bytes' expected)".format(type(data)))
