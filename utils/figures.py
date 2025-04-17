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
    img = pil_img.convert("RGBA")
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    h, w = img_cv.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)

    bgr_color = (fill_color[2], fill_color[1], fill_color[0])

    cv2.floodFill(img_cv, mask, seed_point, bgr_color)

    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    filled_img = Image.fromarray(img_rgb).convert("RGBA")



    return filled_img