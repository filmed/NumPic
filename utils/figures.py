from PIL import Image, ImageDraw
import cv2
import numpy as np


def draw_ellipse(image, bounds, width=3, outlinecolor='white', fillcolor = 'black', antialias=4):

    _image = image.copy()
    mask = Image.new(
        size=[int(dim * antialias) for dim in image.size],
        mode='L', color='black')
    draw = ImageDraw.Draw(mask)

    for offset, fill in (width/-2.0, 'white'), (width/2.0, 'black'):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        draw.ellipse([left, top, right, bottom], fill=fill)

    mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    # paste outline
    _image.paste(outlinecolor, mask=mask)

    mask = Image.new(
        size=[int(dim * antialias) for dim in image.size],
        mode='L', color='black')
    draw = ImageDraw.Draw(mask)

    for offset, fill in (width / -2.0, 'black'), (width / 2.0, 'white'):
        left, top = [(value + offset) * antialias for value in bounds[:2]]
        right, bottom = [(value - offset) * antialias for value in bounds[2:]]
        draw.ellipse([left, top, right, bottom], fill=fill)

    mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    # paste filling
    _image.paste(fillcolor, mask=mask)

    return _image


def fill_intervals(_img: Image, _start_point, _fill_color):
    _count = 0
    _w, _h = _img.size
    _stack = [_start_point]
    _start_color = _img.getpixel(_start_point)

    if _start_color == _fill_color:
        return

    while _stack:
        _x, _y = _stack.pop()
        _xLeft, _xRight = _x, _x + 1

        # fill to the left
        while _xLeft >= 0 and _img.getpixel((_xLeft, _y)) == _start_color:
            _img.putpixel((_xLeft, _y), _fill_color)
            _count += 1
            _xLeft -= 1
        _xLeft += 1

        while _xRight < _w and _img.getpixel((_xRight, _y)) == _start_color:
            _img.putpixel((_xRight, _y), _fill_color)
            _count += 1
            _xRight += 1

        _xRight -= 1

        # lower
        if _y - 1 >= 0:
            fragment = None
            for x in range(_xLeft, _xRight + 1):
                _color = _img.getpixel((x, _y - 1))
                if _color != _fill_color and _color == _start_color:
                    fragment = x
                else:
                    if fragment:
                        _stack.append((fragment, _y - 1))
                        fragment = None
            if fragment:
                _stack.append((fragment, _y - 1))

        # upper
        if _y + 1 < _h:
            fragment = None
            for x in range(_xLeft, _xRight + 1):
                _color = _img.getpixel((x, _y + 1))
                if _color != _fill_color and _color == _start_color:
                    fragment = x
                else:
                    if fragment:
                        _stack.append((fragment, _y + 1))
                        fragment = None
            if fragment:
                _stack.append((fragment, _y + 1))

    return _count


def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
    img_rgba = pil_img.convert("RGBA")
    img_np = np.array(img_rgba)

    r, g, b, a = cv2.split(img_np)
    img_bgr = cv2.merge([b, g, r])

    mask = np.zeros((a.shape[0] + 2, a.shape[1] + 2), np.uint8)
    bgr_color = (fill_color[2], fill_color[1], fill_color[0])
    lo_diff = (10, 10, 10)
    up_diff = (10, 10, 10)

    # cv2 floodfill alg
    cv2.floodFill(img_bgr, mask, seed_point, bgr_color, lo_diff, up_diff, 8)

    filled_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    if a[seed_point[1], seed_point[0]] == 0:
        a[mask[1:-1, 1:-1] == 1] = 255

    filled_rgba = np.dstack((filled_rgb, a))

    # заносим изменения сразу на изображение
    pil_img.paste(Image.fromarray(filled_rgba, "RGBA"))


def get_text_size(_text, _font):
    ascent, descent = _font.geometrics()
    width = _font.getmask(_text).getbbox()[2]
    height = _font.getmask(_text).getbbox()[3] + descent

    return width, height


