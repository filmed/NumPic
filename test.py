def hex2rgb(_hex):
    _hex = _hex.replace("#", "")
    return int(_hex[:2], 16), int(_hex[2:4], 16), int(_hex[4:], 16)

color = "#000000"

print(hex2rgb(color))