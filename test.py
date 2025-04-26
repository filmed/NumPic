import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
from customtkinter import filedialog
from PIL import Image
import joblib
from utils.clust_test import export_contours_to_svg, contours_from_labels, draw_vector_contours, smooth_contour, cluster_image_fast
import pandas as pd


count = 4
ksize = 9
# start_centers = [(255, 255, 0), (0, 0, 255), (0, 100, 150), (200, 0, 50)]
start_centers = [(255, 255, 0), (0, 100, 150)]

valid_types = ["jpg", "jpeg", "png", "bmp"]
file_types = [("Images", "".join(f'*.{valid_type} ' for valid_type in valid_types).strip()), ("All files", "*.*")]
_dir = os.path.expanduser("C:/Users/User/Desktop")

file_path = filedialog.askopenfilename(title="Select an image", initialdir=_dir, filetypes=file_types)

if file_path and os.path.isfile(file_path):
    file_type = os.path.splitext(file_path)[1][1:].lower()
    if file_type in valid_types:
        current_file = file_path
        image = Image.open(current_file)
        w, h = image.size
        image_np = np.array(image)
        image_np = cv2.GaussianBlur(image_np, (ksize, ksize), 0)
        start_centers_BGR = [(b, g, r) for (r, g, b) in start_centers]

        segmented_image_np, (retvals, labels, centers) = cluster_image_fast(image_np, count, start_centers_BGR)
        labels_2d = labels.reshape((h, w))
        segmented_image = Image.fromarray(segmented_image_np)

        # contours_vec = extract_vector_contours_from_labels(labels_2d)
        contours = contours_from_labels(labels_2d, _type=cv2.CHAIN_APPROX_SIMPLE)

        new_width, new_height = int(w / 0.5), int(h / 0.5)
        scale_x = new_width / w
        scale_y = new_height / h

        smoothed = contours
        base_cnt = draw_vector_contours((new_width, new_height), smoothed)
        cv2.imshow(f"base_cnt", base_cnt)

        model = joblib.load("epsilon_model3.joblib")
        eps = 0.002
        first = smoothed[0]
        avg_len = 0
        for _ in range(1):
            result = []
            for index, _cnt in enumerate(smoothed):
                cur_len = int(cv2.arcLength(_cnt, True))
                cur_area = int(cv2.contourArea(_cnt))
                cur_count = len(_cnt)
                cur_density = cur_len / cur_count
                cur_x = pd.DataFrame([[cur_len, cur_area, cur_count, cur_density]], columns=["len", "area", "count", "density"])
                cur_pred = model.predict(cur_x)
                eps = np.expm1(cur_pred)[0]
                current, key_angles_cnt = smooth_contour(_cnt, eps, 0.995)
                result.append(current)
            smoothed = result

        # 4. Визуализация
        plt.figure(figsize=(12, 6))

        # Исходный контур
        plt.subplot(121)
        plt.title("Исходный контур")
        for contour in contours:
            pts = contour.squeeze(1)
            plt.plot(pts[:, 0], pts[:, 1], 'r-', linewidth=2)
            plt.scatter(pts[:, 0], pts[:, 1], c='blue', s=30)
        plt.gca().invert_yaxis()
        plt.grid(True)

        # Сглаженный контур
        plt.subplot(122)
        plt.title("Сглаженный контур")
        for contour in smoothed:
            pts = contour.squeeze(1)
            plt.plot(pts[:, 0], pts[:, 1], 'g-', linewidth=2)
            plt.scatter(pts[:, 0], pts[:, 1], c='red', s=50, marker='x')
        plt.gca().invert_yaxis()
        plt.grid(True)

        plt.tight_layout()
        plt.show()

        contoured_image_array = draw_vector_contours((new_width, new_height), contours)
        contoured_image = Image.fromarray(contoured_image_array)

        export_contours_to_svg(
            contours=contours,
            filename="contours.svg",
            width=new_width,
            height=new_height,
            scale_x=scale_x,
            scale_y=scale_y,
            smooth=False,
            stroke_color="black",
            stroke_width=1,
            stroke_opacity=1.0,
            fill=False
        )


        smoothed_contoured_image_array = draw_vector_contours((new_width, new_height), smoothed)
        smoothed_contoured_image = Image.fromarray(smoothed_contoured_image_array)

        export_contours_to_svg(
            contours=smoothed,
            filename="contours_smoothed.svg",
            width=new_width,
            height=new_height,
            scale_x=scale_x,
            scale_y=scale_y,
            smooth=False,
            stroke_color="black",
            stroke_width=1,
            stroke_opacity=1.0,
            fill=False
        )


