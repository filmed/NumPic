from scipy.interpolate import splprep, splev
import numpy as np
import xml.etree.ElementTree as ET
import cv2

def draw_vector_contours(image_size, contours):
    image_array = 255 * np.ones((image_size[1], image_size[0], 3), dtype=np.uint8)  # (h, w)
    cv2.drawContours(image_array, contours, -1, (0, 0, 0), 1)
    return image_array

def maximin_centers_fast(img, k):
    pixels = img.reshape(-1, 3).astype(np.float32)
    centers = np.empty((k, 3), dtype=np.float32)
    centers[0] = pixels[0]
    dists = np.linalg.norm(pixels - centers[0], axis=1)
    for i in range(1, k):
        idx = np.argmax(dists)
        centers[i] = pixels[idx]
        new_dists = np.linalg.norm(pixels - centers[i], axis=1)
        dists = np.minimum(dists, new_dists)
    return centers


def calc_labels_fast(img, centers):
    pixels = img.reshape(-1, 3).astype(np.float32)
    centers = np.array(centers, dtype=np.float32)
    dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
    return np.argmin(dists, axis=1).reshape(-1, 1).astype(np.int32)

def contours_from_labels(labels_2d, _type=cv2.CHAIN_APPROX_NONE):
    _contours = []
    for label in np.unique(labels_2d):
        mask = np.uint8(labels_2d == label) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, _type)

        for contour in contours:
            _contours.append(contour)  # без обёртки в tuple

    return _contours  # list of ndarray(N,1,2)

def cluster_image_fast(img, k, init_centers=None, iters=10, acc=1.0):
    img_rgb = img[:, :, :3]
    pixel_vals = img_rgb.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, iters, acc)

    if init_centers:
        k = len(init_centers)
        centers = np.array(init_centers, dtype=np.float32)
        labels = calc_labels_fast(img_rgb, centers)

        retval, labels_out, centers_out = cv2.kmeans(
            pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
        )
        centers_out = centers.reshape(-1, 3)

    else:
        centers = maximin_centers_fast(img_rgb, k)
        print(f"centers: {centers}", end="")
        labels = calc_labels_fast(img_rgb, centers)

        retval, labels_out, centers_out = cv2.kmeans(
            pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
        )

    centers_out = np.uint8(centers_out)
    segmented = centers_out[labels_out.flatten()]
    segmented_img = segmented.reshape(img_rgb.shape)

    return segmented_img, (retval, labels_out, centers_out)

def smooth_contour(_contour, _epsilon_factor=0.005, _min_angle_cos=0.99):
    points = _contour.squeeze(1)

    mask = np.ones(len(points), dtype=bool)
    mask[1:] = np.any(points[1:] != points[:-1], axis=1)

    # аппроксимация
    epsilon = _epsilon_factor * cv2.arcLength(_contour, True)
    approx = cv2.approxPolyDP(_contour, epsilon, True).squeeze(1)

    # отбор угловых точек
    if len(approx) > 2:
        vec1 = approx[:-2] - approx[1:-1]
        vec2 = approx[2:] - approx[1:-1]
        norm_prod = np.linalg.norm(vec1, axis=1) * np.linalg.norm(vec2, axis=1)
        valid = norm_prod > 1e-8
        dots = np.einsum('ij,ij->i', vec1, vec2)
        with np.errstate(divide='ignore', invalid='ignore'):
            cos_angles = np.where(valid, dots / norm_prod, 0)
        mask = np.abs(cos_angles) < _min_angle_cos
        key_angles_count = np.sum(mask)
        optimized = np.vstack([approx[0], approx[1:-1][mask], approx[-1]])
    else:
        optimized = approx
        key_angles_count = 0

    # замыкание
    if not is_closed(optimized):
        optimized = np.vstack([optimized, optimized[0]])


    return optimized.reshape(-1, 1, 2), key_angles_count

def is_closed(contour, atol=0.5):
    return np.allclose(contour[0], contour[-1], atol=atol)

def export_contours_to_svg(
        contours,
        filename,
        width,
        height,
        scale_x=1.0,
        scale_y=1.0,
        smooth=True,
        stroke_color="black",
        stroke_width=1,
        stroke_opacity=1.0,
        fill=False,
        fill_color="none",
        fill_opacity=0.0,
        simplify_eps=1.0,
        add_numbers=True,
        font_size=12,
        number_color="red"
):

    def to_svg_path_from_contour(contour):
        contour = np.array(contour).reshape(-1, 2)
        if len(contour) < 3:
            return "", None

        x = contour[:, 0] * scale_x
        y = contour[:, 1] * scale_y

        center_x = np.mean(x)
        center_y = np.mean(y)

        if smooth and len(x) >= 4:
            try:
                tck, u = splprep([x, y], s=simplify_eps)
                u_fine = np.linspace(0, 1, num=len(x) * 4)
                x_fine, y_fine = splev(u_fine, tck)
                points = list(zip(x_fine, y_fine))
            except Exception:
                points = list(zip(x, y))  # fallback
        else:
            points = list(zip(x, y))

        d = f"M {points[0][0]:.2f},{points[0][1]:.2f} "
        for px, py in points[1:]:
            d += f"L {px:.2f},{py:.2f} "
        return d, (center_x, center_y)

    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(width),
        "height": str(height),
        "viewBox": f"0 0 {width} {height}",
        "version": "1.1"
    })

    # Добавим фон
    ET.SubElement(svg, "rect", {
        "x": "0", "y": "0",
        "width": str(width),
        "height": str(height),
        "fill": "white"
    })

    for i, contour_data in enumerate(contours):
        if isinstance(contour_data, tuple):
            contour = contour_data[1]
        else:
            contour = contour_data

        path_d, center = to_svg_path_from_contour(contour)
        if not path_d:
            continue

        style = {
            "d": path_d,
            "stroke": stroke_color,
            "stroke-width": str(stroke_width),
            "stroke-opacity": str(stroke_opacity),
            "fill": fill_color if fill else "none",
            "fill-opacity": str(fill_opacity if fill else 0.0)
        }
        ET.SubElement(svg, "path", style)

        if add_numbers and center:
            text_style = {
                "x": str(center[0]),
                "y": str(center[1]),
                "font-size": str(font_size),
                "fill": number_color,
                "text-anchor": "middle",
                "dominant-baseline": "middle"
            }
            text = ET.SubElement(svg, "text", text_style)
            text.text = str(i + 1)  # Нумерация с 1

    tree = ET.ElementTree(svg)
    tree.write(filename, encoding="utf-8", xml_declaration=True)