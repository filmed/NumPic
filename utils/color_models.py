def hex2rgb(_hex):
    _hex = _hex.replace("#", "")
    return int(_hex[:2], 16), int(_hex[2:4], 16), int(_hex[4:], 16)


def rgb2hex(_rgb):
    return "#" + ''.join(f'{i:02X}' for i in _rgb)