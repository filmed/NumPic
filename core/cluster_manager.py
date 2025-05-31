from utils.clust_test import cluster_image_fast, smooth_contour, find_region_contours_with_hierarchy, merge_small_regions
import numpy as np
from utils.color_models import hex2rgb, rgb2hex
from widgets.pallet_clusters_centers_frame import PalletClustersCentersFrame
import cv2
from PIL import Image
import joblib
import pandas as pd

class ClusterManager:
    def __init__(self, event_bus, editor_use_zone, render_use_zone,
                 centers_frame: PalletClustersCentersFrame, count_entry):
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

    def smooth_contour_tree_outer_only(self, node, cluster_manager):
        node["contour"] = cluster_manager.get_smoothed(node["contour"])

        for child in node["children"]:
            self.smooth_contour_tree_outer_only(child, cluster_manager)

    def collect_contours(self, node, outers, holes, is_outer=True):
        if is_outer:
            outers.append(node["contour"])
        else:
            holes.append(node["contour"])
        for child in node["children"]:
            self.collect_contours(child, outers, holes, is_outer=not is_outer)

    def get_smoothed(self, contour):
        length = cv2.arcLength(contour, True)
        area = cv2.contourArea(contour)
        count = len(contour)
        density = length / (count or 1)
        df = pd.DataFrame([[length, area, count, density]],
                          columns=["len", "area", "count", "density"])
        pred = self.model.predict(df)
        eps = np.expm1(pred[0])
        smoothed, _ = smooth_contour(contour, eps, 0.995)
        return smoothed

    def on_cluster_selected(self, _data=None):
        if not _data or not self.editor_use_zone.composited_img:
            return
        w, h = self.editor_use_zone.composited_img.size
        image_np = np.array(self.editor_use_zone.composited_img)

        start_centers = list(hex2rgb(color) for color in self.centers_frame.get_centers())

        if start_centers:
            count = None
        else:
            try:
                count = int(self.count_entry.get())
            except ValueError:
                print("Невалидное число кластеров")
                return
            if count < 1:
                print("Число кластеров должно быть >= 1")
                return

        if not (start_centers or count):
            return

        segmented_np, (ret, labels_flat, centers) = cluster_image_fast(image_np, count, start_centers)
        segmented_image = Image.fromarray(segmented_np)
        labels_2d = labels_flat.reshape((h, w))
        labels_2d = merge_small_regions(labels_2d, 20)

        regions = find_region_contours_with_hierarchy(labels_2d, approx_method=cv2.CHAIN_APPROX_SIMPLE)

        for label, contour_trees in regions.items():
            for root_node in contour_trees:
                self.smooth_contour_tree_outer_only(root_node, self)

        smoothed_outers = []
        smoothed_holes = []

        for contour_trees in regions.values():
            for root_node in contour_trees:
                self.collect_contours(root_node, smoothed_outers, smoothed_holes)

        # Отрисовка
        canvas = 255 * np.ones((h, w, 3), dtype=np.uint8)
        cv2.drawContours(canvas, smoothed_outers, -1, (0, 0, 0), 1)
        cv2.drawContours(canvas, smoothed_holes, -1, (255, 255, 255), 1)

        smoothed_contoured_image = Image.fromarray(canvas)

        self.current_contours = regions
        self.current_centers = list(rgb2hex(tuple(color)) for color in centers)
        self.segmented_image = segmented_image

        self.event_bus.send_state("centers_delete_all", True)
        for _center in self.current_centers:
            self.centers_frame.add_center(_center)

        self.event_bus.send_state("layer_delete_all", True)
        self.event_bus.send_state("file_opened", (segmented_image, "Segmented image"))
        self.render_use_zone.set_image((smoothed_contoured_image, "Contours"))

        self.event_bus.send_state("clusters_changed", (self.current_contours, self.current_centers, self.segmented_image))

