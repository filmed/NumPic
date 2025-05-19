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


# def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
#     img = pil_img.convert("RGBA")
#     img_np = np.array(img)
#     img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
#
#     h, w = img_cv.shape[:2]
#     mask = np.zeros((h + 2, w + 2), np.uint8)
#
#     bgr_color = (fill_color[2], fill_color[1], fill_color[0])
#
#     cv2.floodFill(img_cv, mask, seed_point, bgr_color)
#
#     img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
#     filled_img = Image.fromarray(img_rgb).convert("RGBA")
#
#     return filled_img

# def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
#     # Конвертируем в RGBA если нужно
#     img = pil_img.convert("RGBA")
#     img_np = np.array(img)
#
#     # Разделяем каналы
#     r, g, b, a = cv2.split(img_np)
#
#     # Создаём 3-канальное изображение для заливки (BGR)
#     img_bgr = cv2.merge([b, g, r])
#
#     # Маска: 1 в непрозрачных пикселях, 0 в прозрачных (граница)
#     mask = np.zeros((img_np.shape[0] + 2, img_np.shape[1] + 2), np.uint8)
#     mask[1:-1, 1:-1] = (a == 0)  # Граница там где прозрачно
#
#     Image.fromarray(img_bgr).save("debug_bgr.png")
#     Image.fromarray(mask * 255).save("debug_mask.png")
#
#     # Цвет заливки (BGR)
#     bgr_color = (fill_color[2], fill_color[1], fill_color[0])
#
#     # Флаг 4 или 8 связности (8 лучше для диагоналей)
#     flags = 8 | cv2.FLOODFILL_MASK_ONLY
#
#     # Выполняем заливку
#     cv2.floodFill(img_bgr, mask, seed_point, bgr_color, flags=flags)
#
#     # Собираем обратно в RGB
#     filled_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
#
#     # Объединяем с оригинальным альфа-каналом
#     filled_rgba = cv2.merge([filled_rgb[:, :, 0],
#                              filled_rgb[:, :, 1],
#                              filled_rgb[:, :, 2],
#                              a])
#
#     return Image.fromarray(filled_rgba, 'RGBA')

#
# def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
#     # Конвертируем в RGBA если нужно
#     img = pil_img.convert("RGBA")
#     img_np = np.array(img)
#
#     # Разделяем каналы
#     r, g, b, a = cv2.split(img_np)
#
#     # Создаём 3-канальное изображение для заливки (BGR)
#     img_bgr = cv2.merge([b, g, r])
#
#     # Маска: 0 - где можно заливать, 1 - границы (прозрачные пиксели)
#     mask = np.zeros((a.shape[0] + 2, a.shape[1] + 2), np.uint8)
#     mask[1:-1, 1:-1] = (a == 0)  # 1 там где прозрачно (граница)
#
#     Image.fromarray(img_bgr).save("debug_bgr.png")
#     Image.fromarray(mask * 255).save("debug_mask.png")
#
#     # Цвет заливки (BGR)
#     bgr_color = (fill_color[2], fill_color[1], fill_color[0])
#
#     # Флаги (8-связность + использование маски)
#     flags = 8 | cv2.FLOODFILL_MASK_ONLY
#
#     # Выполняем заливку
#     cv2.floodFill(img_bgr, mask, seed_point, bgr_color, flags=flags)
#
#     # Собираем обратно в RGBA
#     filled_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
#     filled_rgba = np.dstack((filled_rgb, a))
#
#     return Image.fromarray(filled_rgba, 'RGBA')


# def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
#     # Преобразуем изображение в RGBA и NumPy-массив
#     img = pil_img.convert("RGBA")
#     img_np = np.array(img)
#
#     # Извлекаем каналы
#     r, g, b, a = cv2.split(img_np)
#
#     # Создаём 3-канальное изображение для заливки
#     img_bgr = cv2.merge([b, g, r])
#
#     # Пустая маска: всё можно заливать
#     mask = np.zeros((a.shape[0] + 2, a.shape[1] + 2), np.uint8)
#
#     bgr_color = (fill_color[2], fill_color[1], fill_color[0])
#
#     flags = 8
#
#     lo_diff = (10, 10, 10)
#     up_diff = (10, 10, 10)
#
#     cv2.floodFill(img_bgr, mask, seed_point, bgr_color, lo_diff, up_diff, flags)
#
#     filled_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
#
#     if a[seed_point[1], seed_point[0]] == 0:
#         a[mask[1:-1, 1:-1] == 1] = 255
#
#     filled_rgba = np.dstack((filled_rgb, a))
#
#     return Image.fromarray(filled_rgba, 'RGBA')



def flood_fill_cv(pil_img: Image.Image, seed_point, fill_color):
    # Конвертация в RGBA и numpy
    img_rgba = pil_img.convert("RGBA")
    img_np = np.array(img_rgba)

    # Каналы
    r, g, b, a = cv2.split(img_np)
    img_bgr = cv2.merge([b, g, r])

    # Маска
    mask = np.zeros((a.shape[0] + 2, a.shape[1] + 2), np.uint8)
    bgr_color = (fill_color[2], fill_color[1], fill_color[0])
    lo_diff = (10, 10, 10)
    up_diff = (10, 10, 10)

    cv2.floodFill(img_bgr, mask, seed_point, bgr_color, lo_diff, up_diff, 8)

    # Конвертация обратно
    filled_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Обновляем альфа, если точка была прозрачной
    if a[seed_point[1], seed_point[0]] == 0:
        a[mask[1:-1, 1:-1] == 1] = 255

    # Объединение
    filled_rgba = np.dstack((filled_rgb, a))

    # Изменение оригинального изображения in-place
    pil_img.paste(Image.fromarray(filled_rgba, "RGBA"))










def get_text_size(_text, _font):
    ascent, descent = _font.geometrics()
    width = _font.getmask(_text).getbbox()[2]
    height = _font.getmask(_text).getbbox()[3] + descent

    return width, height


