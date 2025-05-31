import numpy as np
import cv2
import svgwrite
import os
from utils.color_models import hex2rgb
from shapely.geometry import Polygon


def calc_text_color(color):
    rgb = hex2rgb(color)
    L = round(rgb[0] * 299 / 1000 + rgb[1] * 587 / 1000 + rgb[2] * 114 / 1000)
    return "#000000" if L > 128 else "#FFFFFF"

def merge_small_regions(labels_2d, min_size):
    labels = labels_2d.copy()
    changed = True

    while changed:
        changed = False
        new_labels = labels.copy()

        for target_label in np.unique(labels):
            mask = (labels == target_label).astype(np.uint8)

            # Поиск связанных компонент
            num_components, comp_labels = cv2.connectedComponents(mask)

            for comp_id in range(1, num_components):
                component_mask = (comp_labels == comp_id)
                comp_size = np.sum(component_mask)

                if comp_size >= min_size:
                    continue

                changed = True

                dilated = cv2.dilate(component_mask.astype(np.uint8), np.ones((3, 3), np.uint8))
                border = dilated & (~component_mask)

                neighbor_labels = labels[border.astype(bool)]
                neighbor_labels = neighbor_labels[neighbor_labels != target_label]

                if len(neighbor_labels) == 0:
                    continue

                new_label = np.bincount(neighbor_labels).argmax()
                new_labels[component_mask] = new_label

        labels = new_labels

    return labels


def find_region_contours_with_hierarchy(labels_2d, approx_method=cv2.CHAIN_APPROX_SIMPLE):
    unique_labels = np.unique(labels_2d)
    regions = {}


    for label in unique_labels:

        mask = np.uint8(labels_2d == label) * 255
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, approx_method)

        if not contours or hierarchy is None:
            regions[label] = []
            continue

        hierarchy = hierarchy[0]
        nodes = []
        used_indices = set()

        for i, (next_i, prev_i, first_child_i, parent_i) in enumerate(hierarchy):
            if i in used_indices:
                continue

            nodes.append({
                "id": i,
                "contour": contours[i],
                "children": [],
                "parent": parent_i,
            })
            used_indices.add(i)


        for node in nodes:
            parent_idx = node["parent"]
            if parent_idx != -1 and parent_idx in used_indices:
                parent_node = next((n for n in nodes if n["id"] == parent_idx), None)
                if parent_node:
                    parent_node["children"].append(node)

        top_level = [n for n in nodes if n["parent"] == -1]
        regions[label] = top_level

    return regions


def find_label_centroid_safe(outer_contour, holes):
    outer_points = outer_contour.reshape(-1, 2)
    hole_points = [h.reshape(-1, 2) for h in holes]

    poly = Polygon(outer_points, hole_points)
    representative = poly.representative_point() # получаем свободную точку

    # проверка не попал ли он в отверстие
    for hole in hole_points:
        hole_poly = Polygon(hole)
        if hole_poly.contains(representative):
            boundary = poly.boundary
            nearest_point = boundary.interpolate(boundary.project(representative))
            return nearest_point.x, nearest_point.y

    return representative.x, representative.y

def render_contour_tree_to_svg(dwg, node, color, label=None):
    def contour_to_path(c):
        pts = c.reshape(-1, 2)
        return "M " + " L ".join(f"{x},{y}" for x, y in pts) + " Z"

    # основная заливка области
    outer_path = contour_to_path(node["contour"])
    hole_paths = [contour_to_path(child["contour"]) for child in node["children"]]

    path = dwg.path(fill=color, stroke='none', fill_rule="evenodd")
    path.push(outer_path)
    for hp in hole_paths:
        path.push(hp)
    dwg.add(path)

    dwg.add(dwg.path(d=outer_path, fill='none', stroke='black', stroke_width=1))


    # метка
    if label is not None:
        holes = [child["contour"] for child in node["children"]]
        cx, cy = find_label_centroid_safe(node["contour"], holes)
        print(color)
        dwg.add(dwg.text(str(label), insert=(cx, cy),
                         fill=calc_text_color(color), style="font-size:5px; font-weight:bold",
                         text_anchor="middle", dominant_baseline="central"))

def export_all_svgs(contours, centers, canvas_size, save_dir):
    w, h = canvas_size

    # filled
    dwg_color = svgwrite.Drawing(size=(w, h))
    for idx, (label, contour_trees) in enumerate(contours.items()):
        for root_node in contour_trees:
            if cv2.contourArea(root_node["contour"]) < 10:
                continue
            color = centers[label]
            print(color)
            render_contour_tree_to_svg(dwg_color, root_node, color, label)
    dwg_color.saveas(os.path.join(save_dir, "paint_by_numbers.svg"))

    # empty
    dwg_outline = svgwrite.Drawing(size=(w, h))
    for idx, (label, contour_trees) in enumerate(contours.items()):
        for root_node in contour_trees:
            if cv2.contourArea(root_node["contour"]) < 10:
                continue
            color = centers[label]
            print(color)
            render_contour_tree_to_svg(dwg_outline, root_node, color="#ffffff", label=label)
    dwg_outline.saveas(os.path.join(save_dir, "paint_by_numbers_outline.svg"))


    # pallet
    dwg_palette = svgwrite.Drawing(size=(400, len(centers)*25 + 20))
    for i, color in enumerate(centers):
        y = 10 + i * 25
        hex_color = color
        text_color = calc_text_color(hex_color)
        print(hex_color)
        dwg_palette.add(dwg_palette.rect(insert=(10, y), size=(30, 20), fill=hex_color, stroke='black'))

        dwg_palette.add(dwg_palette.text(
            str(i), insert=(25, y + 10),
            fill=text_color,
            style="font-size:10px; font-weight:bold",
            text_anchor="middle", dominant_baseline="central"
        ))

        dwg_palette.add(dwg_palette.text(
            hex_color, insert=(50, y + 12),
            fill="black",
            style="font-size:10px;",
            dominant_baseline="central"
        ))
    dwg_palette.saveas(os.path.join(save_dir, "paint_by_numbers_palette.svg"))


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
            _contours.append(contour)

    return _contours  # list of ndarray(N,1,2)


def cluster_image_fast(img, k=None, init_centers=None, iters=10, acc=1.0):
    img_rgb = img[:, :, :3]
    pixel_vals = img_rgb.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, iters, acc)

    # кластеризация по начальным центрам
    if init_centers:
        k = len(init_centers)
        centers = np.array(init_centers, dtype=np.float32)
        labels = calc_labels_fast(img_rgb, centers)

        retval, labels_out, centers_out = cv2.kmeans(
            pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
        )
        centers_out = centers.reshape(-1, 3)

    # кластеризация с предварительным вычислением центров
    elif k:
        centers = maximin_centers_fast(img_rgb, k)
        labels = calc_labels_fast(img_rgb, centers)

        retval, labels_out, centers_out = cv2.kmeans(
            pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
        )
    else:
        return

    centers_out = np.uint8(centers_out)
    segmented = centers_out[labels_out.flatten()]
    segmented_img = segmented.reshape(img_rgb.shape)

    return segmented_img, (retval, labels_out, centers_out)


def draw_vector_contours(image_size, contours):
    image_array = 255 * np.ones((image_size[1], image_size[0], 3), dtype=np.uint8)  # (h, w)
    cv2.drawContours(image_array, contours, -1, (0, 0, 0), 1)
    return image_array

def smooth_contour(_contour, _epsilon_factor=0.005, _min_angle_cos=0.99):
    points = _contour.squeeze(1)

    mask = np.ones(len(points), dtype=bool)
    mask[1:] = np.any(points[1:] != points[:-1], axis=1)

    # (Ramer–Douglas–Peucker algorithm)
    epsilon = _epsilon_factor * cv2.arcLength(_contour, True)
    approx = cv2.approxPolyDP(_contour, epsilon, True).squeeze(1)

    # анализ угловых точек
    if len(approx) > 2:
        vec1 = approx[:-2] - approx[1:-1]
        vec2 = approx[2:] - approx[1:-1]
        # вычисление косинусов для всех углов
        norm_prod = np.linalg.norm(vec1, axis=1) * np.linalg.norm(vec2, axis=1)
        valid = norm_prod > 1e-8
        dots = np.einsum('ij,ij->i', vec1, vec2)
        with np.errstate(divide='ignore', invalid='ignore'):
            cos_angles = np.where(valid, dots / norm_prod, 0)
        # дропаю неудовлетворяющие условию
        mask = np.abs(cos_angles) < _min_angle_cos
        key_angles_count = np.sum(mask)
        optimized = np.vstack([approx[0], approx[1:-1][mask], approx[-1]])
    else:
        optimized = approx
        key_angles_count = 0

    if not is_closed(optimized):
        optimized = np.vstack([optimized, optimized[0]])


    return optimized.reshape(-1, 1, 2), key_angles_count


def is_closed(contour, atol=0.5):
    return np.allclose(contour[0], contour[-1], atol=atol)





















#
#
# # def cluster_image_fast(img, k, init_centers=None, iters=10, acc=1.0, merge_factor=5):
# #     img_rgb = img[:, :, :3]
# #
# #     if init_centers:
# #         # Используем предоставленные центры
# #         palette = [tuple(map(int, c)) for c in init_centers]
# #         k = len(palette)
# #     elif k:
# #         # Генерируем палитру с помощью улучшенного алгоритма
# #         all_colours = [tuple(map(int, img[y, x])) for y in range(img.shape[0]) for x in range(img.shape[1])]
# #         palette = cluster_colors(all_colours, k, max_n=10000, max_i=iters)
# #     else:
# #         return None
# #
# #     # Применяем медианный фильтр
# #     img_pil = Image.fromarray(img_rgb)
# #     img_filtered = img_pil.filter(ImageFilter.MedianFilter(size=3))
# #     img_filtered_np = np.array(img_filtered)
# #
# #     # Цветизация каждого пикселя в ближайший цвет палитры
# #     labels = np.zeros((img.shape[0], img.shape[1]), dtype=np.int32)
# #     for y in range(img.shape[0]):
# #         for x in range(img.shape[1]):
# #             labels[y, x] = colourize_safe(img_filtered_np[y, x], palette)
# #
# #     # Сегментация и объединение регионов
# #     regions = segment_image(img_filtered_np, labels, k, int(k * merge_factor))
# #
# #     # Преобразуем центры в numpy array
# #     centers = np.array(palette, dtype=np.uint8)
# #
# #     # Создаем сегментированное изображение
# #     segmented = np.zeros_like(img_rgb)
# #     for y in range(img.shape[0]):
# #         for x in range(img.shape[1]):
# #             segmented[y, x] = centers[labels[y, x]]
# #
# #     return segmented, (None, labels.reshape(-1, 1), centers)
#
#
# # def cluster_image_fast(img, k, init_centers=None, iters=10, acc=1.0):
# #     img_rgb = img[:, :, :3]
# #     pixel_vals = img_rgb.reshape(-1, 3).astype(np.float32)
# #
# #     criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, iters, acc)
# #
# #     if init_centers:
# #         k = len(init_centers)
# #         centers = np.array(init_centers, dtype=np.float32)
# #         labels = calc_labels_fast(img_rgb, centers)
# #
# #         retval, labels_out, centers_out = cv2.kmeans(
# #             pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
# #         )
# #         centers_out = centers.reshape(-1, 3)
# #
# #     elif k:
# #         centers = maximin_centers_fast(img_rgb, k)
# #         labels = calc_labels_fast(img_rgb, centers)
# #
# #         retval, labels_out, centers_out = cv2.kmeans(
# #             pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS
# #         )
# #     else:
# #         return None
# #
# #     centers_out = np.uint8(centers_out)
# #     segmented = centers_out[labels_out.flatten()]
# #     segmented_img = segmented.reshape(img_rgb.shape)
# #
# #     return segmented_img, (retval, labels_out, centers_out)
#
# def cluster_image_fast(img, k=None, init_centers=None, iters=10, acc=1.0):
#     img_rgb = img[:, :, :3]
#     pixel_vals = img_rgb.reshape(-1, 3).astype(np.float32)
#     criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, iters, acc)
#
#     if init_centers is not None:
#         k = len(init_centers)
#         centers = np.array(init_centers, dtype=np.float32)
#         labels = calc_labels_fast(img_rgb, centers)
#
#         _, labels_out, centers_out = cv2.kmeans(pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS)
#         centers_out = centers.reshape(-1, 3)
#
#     elif k is not None and k > 0:
#         centers = maximin_centers_fast(img_rgb, k)
#         labels = calc_labels_fast(img_rgb, centers)
#         _, labels_out, centers_out = cv2.kmeans(pixel_vals, k, labels, criteria, 1, cv2.KMEANS_USE_INITIAL_LABELS)
#
#     else:
#         return None
#
#     # Применяем медианный фильтр для сглаживания
#     img_pil = Image.fromarray(img_rgb)
#     img_filtered = img_pil.filter(ImageFilter.MedianFilter(size=3))
#     img_filtered_np = np.array(img_filtered)
#
#     # Обновляем цвета с учетом фильтрации
#     centers_out = np.uint8(centers_out)
#     for y in range(img_filtered_np.shape[0]):
#         for x in range(img_filtered_np.shape[1]):
#             img_filtered_np[y, x] = centers_out[labels_out.reshape(img_rgb.shape[:2])[y, x]]
#
#     return img_filtered_np, (None, labels_out, centers_out)
#
# def maximin_centers_fast(img, k):
#     pixels = img.reshape(-1, 3).astype(np.float32)
#     centers = np.empty((k, 3), dtype=np.float32)
#     centers[0] = pixels[0]
#     dists = np.linalg.norm(pixels - centers[0], axis=1)
#     for i in range(1, k):
#         idx = np.argmax(dists)
#         centers[i] = pixels[idx]
#         new_dists = np.linalg.norm(pixels - centers[i], axis=1)
#         dists = np.minimum(dists, new_dists)
#     return centers
#
#
# def calc_labels_fast(img, centers):
#     pixels = img.reshape(-1, 3).astype(np.float32)
#     centers = np.array(centers, dtype=np.float32)
#     dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
#     return np.argmin(dists, axis=1).reshape(-1, 1).astype(np.int32)
#
#
#
# #
# # def maximin_centers_fast(img, k):
# #     """Улучшенная инициализация центров с гарантией разных цветов"""
# #     pixels = img.reshape(-1, 3).astype(np.float32)
# #     centers = np.empty((k, 3), dtype=np.float32)
# #
# #     # Первый центр - случайная точка
# #     centers[0] = pixels[np.random.randint(0, len(pixels))]
# #
# #     for i in range(1, k):
# #         # Вычисляем расстояния до ближайшего центра для всех точек
# #         dists = np.array([min(np.sum((p - centers[j]) ** 2) for j in range(i))
# #                           for p in pixels])
# #
# #         # Выбираем точку с максимальным расстоянием
# #         new_center_idx = np.argmax(dists)
# #         centers[i] = pixels[new_center_idx]
# #
# #         # Удаляем выбранный цвет из рассмотрения, чтобы избежать дублирования
# #         pixels = np.delete(pixels, new_center_idx, axis=0)
# #
# #     return centers
#
#
# #
# # def calc_labels_fast(img, centers):
# #     """Вычисление меток для каждого пикселя"""
# #     pixels = img.reshape(-1, 3).astype(np.float32)
# #     centers = np.array(centers, dtype=np.float32)
# #
# #     # Векторизованное вычисление расстояний
# #     dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
# #     return np.argmin(dists, axis=1).reshape(-1, 1).astype(np.int32)
#
# #
# # def cluster_image_fast(img, k, init_centers=None, iters=10, acc=1.0, merge_factor=5):
# #     img_rgb = img[:, :, :3]
# #
# #     if init_centers:
# #         # Используем предоставленные центры
# #         palette = [tuple(map(int, c)) for c in init_centers]
# #         k = len(palette)
# #     elif k:
# #         # Генерируем палитру с помощью улучшенного алгоритма
# #         all_colours = [tuple(map(int, img[y, x])) for y in range(img.shape[0]) for x in range(img.shape[1])]
# #         palette = cluster_colors(all_colours, k, max_n=10000, max_i=iters)
# #     else:
# #         return None
# #
# #     # Применяем медианный фильтр
# #     img_pil = Image.fromarray(img_rgb)
# #     img_filtered = img_pil.filter(ImageFilter.MedianFilter(size=3))
# #     img_filtered_np = np.array(img_filtered)
# #
# #     # Цветизация каждого пикселя в ближайший цвет палитры
# #     labels = np.zeros((img.shape[0], img.shape[1]), dtype=np.int32)
# #     for y in range(img.shape[0]):
# #         for x in range(img.shape[1]):
# #             labels[y, x] = colourize_safe(img_filtered_np[y, x], palette)
# #
# #     # Сегментация и объединение регионов
# #     regions = segment_image(img_filtered_np, labels, k, int(k * merge_factor))
# #
# #     # Преобразуем центры в numpy array
# #     centers = np.array(palette, dtype=np.uint8)
# #
# #     # Создаем сегментированное изображение
# #     segmented = np.zeros_like(img_rgb)
# #     for y in range(img.shape[0]):
# #         for x in range(img.shape[1]):
# #             segmented[y, x] = centers[labels[y, x]]
# #
# #     return segmented, (None, labels.reshape(-1, 1), centers)
#
#
# def cluster_colors(colours, k, max_n=10000, max_i=10):
#     """Улучшенный алгоритм кластеризации цветов"""
#
#     def color_distance(c1, c2):
#         # Используем более стабильное вычисление расстояния
#         return sum((float(a) - float(b)) ** 2 for a, b in zip(c1, c2))
#
#     def mean_color(colours):
#         if not colours:
#             return (0, 0, 0)
#         n = len(colours)
#         # Используем float для промежуточных вычислений
#         return tuple(int(round(sum(float(c[i]) for c in colours) / n)) for i in range(3))
#
#     # Берем подвыборку, если цветов слишком много
#     if len(colours) > max_n:
#         colours = random.sample(colours, max_n)
#
#     # Инициализируем центроиды
#     centroids = random.sample(colours, min(k, len(colours)))
#
#     for i in range(max_i):
#         # Назначение цветов ближайшим центроидам
#         clusters = {cen: [] for cen in centroids}
#         for color in colours:
#             closest = min(centroids, key=lambda cen: color_distance(color, cen))
#             clusters[closest].append(color)
#
#         # Пересчет центроидов
#         new_centroids = []
#         for cen in centroids:
#             cluster_colors = clusters[cen]
#             if cluster_colors:  # Проверяем, что кластер не пустой
#                 new_centroids.append(mean_color(cluster_colors))
#             else:
#                 # Если кластер пуст, оставляем старый центроид
#                 new_centroids.append(cen)
#
#         # Проверка на сходимость
#         if set(new_centroids) == set(centroids):
#             break
#
#         centroids = new_centroids
#
#     return centroids
#
#
# def colourize_safe(colour, palette):
#     """Находит ближайший цвет в палитре с защитой от переполнения"""
#     min_dist = float('inf')
#     best_idx = 0
#
#     for idx, pal_color in enumerate(palette):
#         # Безопасное вычисление расстояния
#         dist = 0
#         for a, b in zip(colour, pal_color):
#             diff = float(a) - float(b)
#             dist += diff * diff
#             if dist > min_dist:
#                 break  # Досрочный выход если уже хуже
#
#         if dist < min_dist:
#             min_dist = dist
#             best_idx = idx
#
#     return best_idx
#
#
# def colourize(colour, palette):
#     """Находит ближайший цвет в палитре"""
#     return min(enumerate(palette), key=lambda x: sum((a - b) ** 2 for a, b in zip(colour, x[1])))[0]
#
#
# def segment_image(img, labels, k, target_regions):
#     """Сегментация изображения с объединением регионов"""
#     size_x, size_y = img.shape[1], img.shape[0]
#     all_coords = [(x, y) for x in range(size_x) for y in range(size_y)]
#
#     # Находим все регионы
#     rest = set(all_coords)
#     cells = []
#
#     while rest:
#         centre = random.sample(rest, 1)[0]
#         region, rest = grow_region(centre, rest, labels)
#         cells.append(region)
#
#     # Сортируем регионы по размеру
#     cells = sorted(cells, key=len, reverse=True)
#
#     # Объединяем маленькие регионы
#     while len(cells) > target_regions:
#         small_cell = cells.pop()
#         neighbors = find_neighbors(small_cell, set(all_coords) - small_cell, labels)
#
#         for big_cell in cells:
#             if big_cell & neighbors:
#                 big_cell |= small_cell
#                 break
#
#     # Обновляем labels после объединения
#     new_labels = np.copy(labels)
#     for i, cell in enumerate(cells):
#         for x, y in cell:
#             new_labels[y, x] = i
#
#     # Преобразуем в формат регионов для find_region_contours
#     unique_labels = np.unique(new_labels)
#     regions = {}
#     for label in unique_labels:
#         mask = np.uint8(new_labels == label) * 255
#         contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
#         if hierarchy is None:
#             continue
#         hierarchy = hierarchy[0]
#         regions[label] = {'outers': [], 'holes': []}
#         for idx, cnt in enumerate(contours):
#             parent = hierarchy[idx][3]
#             if parent < 0:
#                 regions[label]['outers'].append(cnt)
#             else:
#                 regions[label]['holes'].append(cnt)
#
#     return regions
#
#
# def grow_region(centre, rest, labels):
#     """Растет регион из начальной точки"""
#     color = labels[centre[1], centre[0]]
#     edge = {centre}
#     region = set()
#
#     while edge:
#         region |= edge
#         rest -= edge
#         new_edge = set()
#         for x, y in edge:
#             for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
#                 nx, ny = x + dx, y + dy
#                 if (nx, ny) in rest and labels[ny, nx] == color:
#                     new_edge.add((nx, ny))
#         edge = new_edge
#
#     return region, rest
#
#
# def find_neighbors(region, rest, labels):
#     """Находит соседей региона"""
#     neighbors = set()
#     for x, y in region:
#         for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
#             nx, ny = x + dx, y + dy
#             if (nx, ny) in rest:
#                 neighbors.add((nx, ny))
#     return neighbors
#
#
#
# #
# # def smooth_contour(_contour, _epsilon_factor=0.005, _min_angle_cos=0.99):
# #     points = _contour.squeeze(1)
# #
# #     if len(points) < 3:
# #         return _contour, 0  # слишком короткий контур — не обрабатываем
# #
# #     epsilon = _epsilon_factor * cv2.arcLength(_contour, True)
# #     approx = cv2.approxPolyDP(_contour, epsilon, True).squeeze(1)
# #
# #     if len(approx) > 2:
# #         vec1 = approx[:-2] - approx[1:-1]
# #         vec2 = approx[2:] - approx[1:-1]
# #         norm_prod = np.linalg.norm(vec1, axis=1) * np.linalg.norm(vec2, axis=1)
# #         valid = norm_prod > 1e-8
# #         dots = np.einsum('ij,ij->i', vec1, vec2)
# #         with np.errstate(divide='ignore', invalid='ignore'):
# #             cos_angles = np.where(valid, dots / norm_prod, 0)
# #         mask = np.abs(cos_angles) < _min_angle_cos
# #         key_angles_count = np.sum(mask)
# #         optimized = np.vstack([approx[0], approx[1:-1][mask], approx[-1]])
# #     else:
# #         optimized = approx
# #         key_angles_count = 0
# #
# #     return optimized.reshape(-1, 1, 2), key_angles_count
#
#
# from scipy.ndimage import binary_dilation, binary_erosion
#
# def filter_small_regions(regions, min_area=50, min_length=20):
#     """
#     Удаляет регионы, у которых суммарная площадь и длина контуров ниже порогов.
#     """
#     filtered = {}
#     for label, data in regions.items():
#         area_sum = sum(cv2.contourArea(c) for c in data['outers'])
#         length_sum = sum(cv2.arcLength(c, True) for c in data['outers'])
#
#         if area_sum >= min_area and length_sum >= min_length:
#             filtered[label] = data
#     return filtered
#
#
# def merge_adjacent_contours(regions, min_dist=1.5):
#     """
#     Удаляет дублирующие контурные участки между соседними регионами.
#     Сравнивает пары контуров и удаляет дубликаты (в пределах min_dist).
#     """
#     from shapely.geometry import LineString
#     from shapely.ops import unary_union
#
#     # Преобразуем все внешние контуры в shapely LineStrings
#     contour_lines = []
#     label_lookup = []
#     for label, data in regions.items():
#         for cnt in data['outers']:
#             if len(cnt) >= 2:
#                 line = LineString(cnt[:, 0, :])
#                 contour_lines.append(line)
#                 label_lookup.append((label, cnt))
#
#     # Объединяем близко расположенные линии
#     merged = unary_union(contour_lines)
#
#     # Строим новые регионы из объединённой геометрии
#     from shapely.geometry import Polygon
#     new_regions = {label: {"outers": [], "holes": []} for label in regions}
#
#     for geom in merged.geoms if hasattr(merged, 'geoms') else [merged]:
#         if isinstance(geom, (Polygon, LineString)):
#             coords = np.array(geom.exterior.coords if hasattr(geom, 'exterior') else geom.coords)
#             cnt = coords.astype(np.int32).reshape(-1, 1, 2)
#
#             # Попробуем отнести его к ближайшему оригинальному региону
#             min_label = None
#             min_dist = float('inf')
#             for label, orig_cnt in label_lookup:
#                 d = cv2.matchShapes(cnt, orig_cnt, 1, 0)
#                 if d < min_dist:
#                     min_dist = d
#                     min_label = label
#
#             if min_label is not None:
#                 new_regions[min_label]['outers'].append(cnt)
#
#     return new_regions
#
#
# def remove_duplicate_borders(labels_2d):
#     """
#     Удаляет дублирующиеся границы между соседними регионами,
#     оставляя только одну границу на стыке.
#     """
#     height, width = labels_2d.shape
#     cleaned_labels = labels_2d.copy()
#
#     kernel = np.ones((3, 3), np.uint8)
#     borders = np.zeros_like(labels_2d, dtype=bool)
#
#     # 1. Найдём все пиксели, граничащие с другим лейблом
#     for y in range(1, height-1):
#         for x in range(1, width-1):
#             val = labels_2d[y, x]
#             neighbors = labels_2d[y-1:y+2, x-1:x+2]
#             if np.any(neighbors != val):
#                 borders[y, x] = True
#
#     # 2. Составим карту ближайшего лейбла к каждому пограничному пикселю
#     label_coords = {}
#     for label in np.unique(labels_2d):
#         ys, xs = np.where(labels_2d == label)
#         coords = np.column_stack((ys, xs))
#         label_coords[label] = coords
#
#     distance_map = np.full((height, width), np.inf)
#     ownership = np.full((height, width), -1)
#
#     for label, coords in label_coords.items():
#         for y, x in coords:
#             for dy in [-1, 0, 1]:
#                 for dx in [-1, 0, 1]:
#                     ny, nx = y + dy, x + dx
#                     if 0 <= ny < height and 0 <= nx < width:
#                         dist = dy*dy + dx*dx
#                         if dist < distance_map[ny, nx]:
#                             distance_map[ny, nx] = dist
#                             ownership[ny, nx] = label
#
#     # 3. Применяем Voronoi-подобную схему
#     for y in range(height):
#         for x in range(width):
#             if borders[y, x]:
#                 cleaned_labels[y, x] = ownership[y, x]
#
#     return cleaned_labels
#
# def find_region_contours(labels_2d):
#     regions = {}
#     unique_labels = np.unique(labels_2d)
#
#     for label in unique_labels:
#         if label < 0:
#             continue  # Пропустить фон, если есть -1
#
#         # Создание бинарной маски для каждой метки
#         mask = np.uint8(labels_2d == label) * 255
#
#         # Найти контуры и иерархии (внешние и внутренние контуры)
#         contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
#
#         if not contours or hierarchy is None:
#             continue
#
#         hierarchy = hierarchy[0]
#         outers = []
#         holes = []
#
#         for idx, cnt in enumerate(contours):
#             parent = hierarchy[idx][3]
#             if parent < 0:
#                 outers.append(cnt)
#             else:
#                 holes.append(cnt)
#
#         regions[label] = {"outers": outers, "holes": holes}
#     return regions
#
#
# def export_paint_by_numbers_svg(
#     regions, centers, filename, width, height,
#     scale_x=1.0, scale_y=1.0,
#     stroke_color="black", stroke_width=1, stroke_opacity=1.0,
#     fill=False, fill_opacity=0.3,
#     font_size=12, number_color="red"
# ):
#
#     svg = ET.Element("svg", {
#         "xmlns": "http://www.w3.org/2000/svg",
#         "width": str(width),
#         "height": str(height),
#         "viewBox": f"0 0 {width} {height}",
#         "version": "1.1"
#     })
#     ET.SubElement(svg, "rect", {
#         "x": "0", "y": "0",
#         "width": str(width), "height": str(height),
#         "fill": "white"
#     })
#
#     # Sort regions by area descending
#     items = []
#     for label, data in regions.items():
#         area_sum = sum(cv2.contourArea(c) for c in data['outers'])
#         items.append((label, data, area_sum))
#     items.sort(key=lambda x: -x[2])
#
#     for num, (label, data, _) in enumerate(items, start=1):
#         fill_color = rgb2hex(tuple(centers[label]))
#         # Draw outer contours
#         for cnt in data['outers']:
#             d, center = to_svg_path_from_contour(cnt, scale_x, scale_y)
#             ET.SubElement(svg, "path", {
#                 "d": d,
#                 "stroke": stroke_color,
#                 "stroke-width": str(stroke_width),
#                 "stroke-opacity": str(stroke_opacity),
#                 "fill": fill_color if fill else "none",
#                 "fill-opacity": str(fill_opacity if fill else 0)
#             })
#         # Draw holes (white fill)
#         for hole in data['holes']:
#             d, _ = to_svg_path_from_contour(hole, scale_x, scale_y)
#             ET.SubElement(svg, "path", {
#                 "d": d,
#                 "stroke": stroke_color,
#                 "stroke-width": str(stroke_width),
#                 "stroke-opacity": str(stroke_opacity),
#                 "fill": "white"
#             })
#         # Add label number in center of largest outer
#         if data['outers']:
#             cnt = max(data['outers'], key=cv2.contourArea)
#             moments = cv2.moments(cnt)
#             if moments['m00'] != 0:
#                 cx = (moments['m10'] / moments['m00']) * scale_x
#                 cy = (moments['m01'] / moments['m00']) * scale_y
#                 text = ET.SubElement(svg, "text", {
#                     "x": f"{cx}",
#                     "y": f"{cy}",
#                     "font-size": str(font_size),
#                     "fill": number_color,
#                     "text-anchor": "middle",
#                     "dominant-baseline": "middle"
#                 })
#                 text.text = str(num)
#
#     tree = ET.ElementTree(svg)
#     tree.write(filename, encoding="utf-8", xml_declaration=True)
#
#
# def to_svg_path_from_contour(contour, scale_x, scale_y):
#     contour = np.array(contour).reshape(-1, 2)
#     if len(contour) < 2:
#         return "", None
#     x = contour[:, 0] * scale_x
#     y = contour[:, 1] * scale_y
#
#     points = list(zip(x, y))
#     d = f"M {points[0][0]:.2f},{points[0][1]:.2f} "
#     for px, py in points[1:]:
#         d += f"L {px:.2f},{py:.2f} "
#     center = (np.mean(x), np.mean(y))
#     return d, center
#
# def draw_vector_contours(image_size, contours):
#     image_array = 255 * np.ones((image_size[1], image_size[0], 3), dtype=np.uint8)  # (h, w)
#     cv2.drawContours(image_array, contours, -1, (0, 0, 0), 1)
#     return image_array
#
# #
# # def maximin_centers_fast(img, k):
# #     pixels = img.reshape(-1, 3).astype(np.float32)
# #     centers = np.empty((k, 3), dtype=np.float32)
# #     centers[0] = pixels[0]
# #     dists = np.linalg.norm(pixels - centers[0], axis=1)
# #     for i in range(1, k):
# #         idx = np.argmax(dists)
# #         centers[i] = pixels[idx]
# #         new_dists = np.linalg.norm(pixels - centers[i], axis=1)
# #         dists = np.minimum(dists, new_dists)
# #     return centers
# #
# #
# # def calc_labels_fast(img, centers):
# #     pixels = img.reshape(-1, 3).astype(np.float32)
# #     centers = np.array(centers, dtype=np.float32)
# #     dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
# #     return np.argmin(dists, axis=1).reshape(-1, 1).astype(np.int32)
#
# #
#
#
# def smooth_contour(_contour, _epsilon_factor=0.005, _min_angle_cos=0.99):
#     points = _contour.squeeze(1)
#
#     mask = np.ones(len(points), dtype=bool)
#     mask[1:] = np.any(points[1:] != points[:-1], axis=1)
#
#     epsilon = _epsilon_factor * cv2.arcLength(_contour, True)
#     approx = cv2.approxPolyDP(_contour, epsilon, True).squeeze(1)
#
#     if len(approx) > 2:
#         vec1 = approx[:-2] - approx[1:-1]
#         vec2 = approx[2:] - approx[1:-1]
#         norm_prod = np.linalg.norm(vec1, axis=1) * np.linalg.norm(vec2, axis=1)
#         valid = norm_prod > 1e-8
#         dots = np.einsum('ij,ij->i', vec1, vec2)
#         with np.errstate(divide='ignore', invalid='ignore'):
#             cos_angles = np.where(valid, dots / norm_prod, 0)
#         mask = np.abs(cos_angles) < _min_angle_cos
#         key_angles_count = np.sum(mask)
#         optimized = np.vstack([approx[0], approx[1:-1][mask], approx[-1]])
#     else:
#         optimized = approx
#         key_angles_count = 0
#
#     # замыкание
#     if not is_closed(optimized):
#         optimized = np.vstack([optimized, optimized[0]])
#
#
#     return optimized.reshape(-1, 1, 2), key_angles_count
#
# def is_closed(contour, atol=0.5):
#     return np.allclose(contour[0], contour[-1], atol=atol)
#
#
#
# # def find_region_contours(labels_2d):
# #     regions = {}
# #     h, w = labels_2d.shape
# #     unique_labels = np.unique(labels_2d)
# #
# #     kernel = np.ones((3, 3), np.uint8)
# #
# #     # Общая карта границ между разными сегментами
# #     boundary_mask = np.zeros_like(labels_2d, dtype=np.uint8)
# #     for label in unique_labels:
# #         mask = (labels_2d == label).astype(np.uint8)
# #         dilated = cv2.dilate(mask, kernel)
# #         boundary_mask |= ((dilated > 0) & (labels_2d != label)).astype(np.uint8)
# #
# #     for label in unique_labels:
# #         mask = (labels_2d == label).astype(np.uint8)
# #
# #         # Удаляем общую границу (эрозия по общему boundary)
# #         mask[boundary_mask > 0] = 0
# #
# #         if np.count_nonzero(mask) == 0:
# #             continue
# #
# #         mask = mask * 255
# #         contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
# #         if hierarchy is None:
# #             continue
# #         hierarchy = hierarchy[0]
# #         regions[label] = {'outers': [], 'holes': []}
# #         for idx, cnt in enumerate(contours):
# #             parent = hierarchy[idx][3]
# #             if parent < 0:
# #                 regions[label]['outers'].append(cnt)
# #             else:
# #                 regions[label]['holes'].append(cnt)
# #     return regions
#
