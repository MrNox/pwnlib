import struct


def p8(data:int) -> bytes:
    assert isinstance(data, int), "{} given, must be 'int')".format(type(data))
    return (data & 0xFF).to_bytes(1, byteorder='little')


def p16(data, byteorder) -> bytes:
    assert isinstance(data, int), "{} given, must be 'int')".format(type(data))

    return (data & 0xFFFF).to_bytes(2, byteorder=byteorder)


def p32(data, byteorder) -> bytes:
    assert isinstance(data, (int, float)), "{} given, must be 'int' or 'float')".format(type(data))


    if isinstance(data, float):
       return struct.pack(

               '{}f'.format('<' if byteorder == 'little' else '>'),
               data)

    return (data & 0xFFFFFFFF).to_bytes(4, byteorder=byteorder)


def p64(data, byteorder) -> bytes:
    assert isinstance(data, (int, float)), "{} given, must be 'int' or 'double'".format(type(data))

    if isinstance(data, float):
       return struct.pack(
               '{}d'.format('<' if byteorder == 'little' else '>'),
               data)

    return (data & 0xFFFFFFFFFFFFFFFF).to_bytes(8, byteorder=byteorder)
