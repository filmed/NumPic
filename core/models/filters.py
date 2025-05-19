

from PIL import ImageFilter

def apply_filters(img, filter_params):
    result = img.copy()

    if not filter_params:
        return result

    if 'blur' in filter_params:
        result = result.filter(ImageFilter.GaussianBlur(radius=filter_params['blur']))

    return result