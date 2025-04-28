from utils.clust_test import cluster_image_fast, contours_from_labels, draw_vector_contours, smooth_contour, export_contours_to_svg
import numpy as np
from utils.color_models import hex2rgb
import cv2
from PIL import Image
import joblib
import pandas as pd


class ClusterManager:
    def __init__(self,
                 event_bus,
                 editor_use_zone,  # Для clustered
                 render_use_zone,  # Для контуров
                 centers_frame,    # PalletClustersCentersFrame
                 count_entry       # CountClustersEntry
                 ):
        self.event_bus = event_bus
        self.editor_use_zone = editor_use_zone
        self.render_use_zone = render_use_zone
        self.centers_frame = centers_frame
        self.count_entry = count_entry
        self.model = joblib.load("epsilon_model3.joblib")

        self.current_contours = None
        self.current_centers = None
        self.segmented_image = None

        self.event_bus.subscribe("cluster_selected", self.on_cluster_selected)


    def on_cluster_selected(self, _data=None):
        if not _data or not self.editor_use_zone.img:
            return
        count = 4
        w, h = self.editor_use_zone.img.size
        image_np = np.array(self.editor_use_zone.img)
        image_np = cv2.GaussianBlur(image_np, (9, 9), 0)
        start_centers = list(hex2rgb(color) for color in self.centers_frame.get_centers())
        # start_centers_BGR = [(b, g, r) for (r, g, b) in start_centers]

        if start_centers:
            count = len(start_centers)
        else:
            try:
                count = int(self.count_entry.get())
            except ValueError:
                print("Невалидное число кластеров")
                return
            if count < 1:
                print("Число кластеров должно быть >= 1")
                return

        segmented_image_np, (retvals, labels, centers) = cluster_image_fast(image_np, count, start_centers)
        labels_2d = labels.reshape((h, w))

        # segmented_image_np_rgb = cv2.cvtColor(segmented_image_np, cv2.COLOR_BGR2RGB)
        # segmented_image = Image.fromarray(segmented_image_np_rgb)
        segmented_image = Image.fromarray(segmented_image_np)

        contours = contours_from_labels(labels_2d, _type=cv2.CHAIN_APPROX_SIMPLE)

        # for svg exporting
        new_width, new_height = int(w / 1), int(h / 1)
        scale_x = new_width / w
        scale_y = new_height / h

        smoothed = contours

        for _ in range(1):
            result = []
            for index, _cnt in enumerate(smoothed):
                cur_len = int(cv2.arcLength(_cnt, True))
                cur_area = int(cv2.contourArea(_cnt))
                cur_count = len(_cnt)
                cur_density = cur_len / cur_count
                cur_x = pd.DataFrame([[cur_len, cur_area, cur_count, cur_density]],
                                     columns=["len", "area", "count", "density"])
                cur_pred = self.model.predict(cur_x)
                eps = np.expm1(cur_pred)[0]
                current, key_angles_cnt = smooth_contour(_cnt, eps, 0.995)
                result.append(current)
            smoothed = result

        smoothed_contoured_image_array = draw_vector_contours((new_width, new_height), smoothed)
        smoothed_contoured_image = Image.fromarray(smoothed_contoured_image_array)

        self.current_contours = smoothed
        self.current_centers = centers
        self.segmented_image = segmented_image

        self.editor_use_zone.set_image(segmented_image)
        self.render_use_zone.set_image(smoothed_contoured_image)

        self.event_bus.send_state("clusters_changed", (self.current_contours,  self.current_centers,  self.segmented_image))

        # export_contours_to_svg(
        #     contours=smoothed,
        #     filename="contours_smoothed.svg",
        #     width=new_width,
        #     height=new_height,
        #     scale_x=scale_x,
        #     scale_y=scale_y,
        #     smooth=False,
        #     stroke_color="black",
        #     stroke_width=1,
        #     stroke_opacity=1.0,
        #     fill=False
        # )