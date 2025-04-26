import customtkinter as ctk
import numpy as np
import colour
import ctypes
from core.event_bus import EventBus
from core.theme_manager import ThemeManager
from core.tool_manager import ToolManager
from core.file_manager import FileManager
from core.focus_manager import FocusManager
from core.models.tools import HandTool, BrushTool, PipetteTool, FillTool, EraseTool, CenterChooserTool

from widgets.base import BaseWidget
from widgets.custom_panel import CustomPanel
from widgets.container_panel import ContainerPanel
from widgets.file_open_button import FileOpenButton
from widgets.file_save_button import FileSaveButton
from widgets.pallet_radio_button_frame import PalletRadioButtonFrame
from widgets.pallet import Pallet
from widgets.pallet_sliders_frame import PalletSlidersFrame
from widgets.pallet_display_frame import PalletDisplayFrame
from widgets.pallet_add_button import PalletAddButton
from widgets.image_renderer import ImageRenderer
from widgets.tool_radio_button_frame import ToolRadioButtonFrame
from widgets.blur_slider import BlurSlider
from widgets.pallet_clusters_centers_frame import PalletClustersCentersFrame
from widgets.count_clusters_entry import CountClustersEntry
from core.models.filters import Blur
from widgets.cluster_button import ClusterButton
from core.cluster_manager import ClusterManager


# Monitor scale factor
scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
ctk.set_widget_scaling(1/scaleFactor)
print(scaleFactor)


class App(BaseWidget, ctk.CTk):
    def __init__(self):
        ctk.CTk.__init__(self)

        #   ---------------------------initialization of logistics and managers----------------------------------------
        self.event_bus = EventBus()
        self.file_manager = FileManager(self.event_bus)
        self.theme_manager = ThemeManager(self.event_bus)
        self.theme_manager.change_theme("new")
        self.focus_manager = FocusManager(self, self.event_bus)

        self.tool_manager = ToolManager(self.event_bus)
        self.tools = {
                        "hand_tool": HandTool(_event_bus=self.event_bus),
                        "brush_tool": BrushTool(_event_bus=self.event_bus),
                        "pipette_tool": PipetteTool(_event_bus=self.event_bus),
                        "fill_tool": FillTool(_event_bus=self.event_bus),
                        "erase_tool": EraseTool(_event_bus=self.event_bus),
                        "center_chooser_tool": CenterChooserTool(_event_bus=self.event_bus),
                      }

        for name, tool in self.tools.items():
            self.tool_manager.add_tool(_name=name, _tool=tool)

        self.blur = Blur(self.event_bus, _is_last=True)

        BaseWidget.__init__(self, _event_bus=self.event_bus)
        #   ---------------------------------------setup a window------------------------------------------------------
        self.title("NumPic")
        self.geometry("1920x1080")

        #   2 rows x 3 columns
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self._grid_padx = 0
        self._grid_pady = 0

        #   -------------------------------------setup ui-----------------------------------------------------
        # TOP panel setup
        self.top_panel = CustomPanel(self, self.event_bus, _is_last=True)
        self.top_panel.grid(row=0, column=0, columnspan=3, sticky='we')

        self.tp_file_open_button = FileOpenButton(self.top_panel, self.event_bus, _is_last=True)
        self.tp_file_open_button.grid(row=0, column=0, padx=(5, 0), pady=(5, 5), sticky='w')

        self.tp_file_save_button = FileSaveButton(self.top_panel, self.event_bus, _is_last=True)
        self.tp_file_save_button.grid(row=0, column=1, padx=(5, 0), pady=(5, 5), sticky='w')

        # LEFT panel setup
        self.left_panel = CustomPanel(self, self.event_bus, _is_last=True)
        self.left_panel.grid(row=1, column=0, sticky='nswe')
        #   2 rows x 1 columns
        self.left_panel.grid_rowconfigure(0, weight=0)
        self.left_panel.grid_rowconfigure(1, weight=0)
        self.left_panel.grid_rowconfigure(2, weight=0)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.left_panel.grid_columnconfigure(0, minsize=280)

        #   плиточная палитра
        self.lp_pallet_radio_button_frame = PalletRadioButtonFrame(self.left_panel, self.event_bus, _is_last=True)
        self.lp_pallet_radio_button_frame.grid(row=0, column=0, padx=(10, 10), pady=(10, 0), sticky='nsew')

        # виджеты палитры
        self.lp_pallet_widgets_container = ContainerPanel(self.left_panel, self.event_bus, _is_last=True)
        self.lp_pallet_widgets_container.grid(row=1, column=0, padx=(10, 10), pady=(30, 0), sticky='nsew')

        #  палитра
        self.lp_pallet_container = ContainerPanel(self.lp_pallet_widgets_container, _event_bus=self.event_bus, _is_last=True)
        self.lp_pallet_container.grid(row=0, column=0, padx=(10, 10), pady=(0, 0), sticky='nsew')

        self.lp_pallet = Pallet(self.lp_pallet_container, self.event_bus, _is_last=True)
        self.lp_pallet.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky='nsew')
        self.lp_pallet_container.grid_propagate(False)
        required_height = self.lp_pallet.canvas_d + 10
        self.lp_pallet_widgets_container.grid_rowconfigure(0, minsize=required_height)

        #  слайдеры
        self.lp_pallet_sliders_frame = PalletSlidersFrame(self.lp_pallet_widgets_container, self.event_bus, _is_last=True)
        self.lp_pallet_sliders_frame.grid(row=1, column=0, padx=(0, 0), pady=(20, 0), sticky="nswe")

        #   контейнер для отображения цвета и кнопки добавления
        self.lp_display_add_container = ContainerPanel(self.lp_pallet_widgets_container, self.event_bus, _is_last=True)
        self.lp_display_add_container.grid(row=2, column=0, padx=(15, 10), pady=(20, 0), sticky="nswe")
        self.lp_display_add_container.grid_columnconfigure(0, weight=1)
        self.lp_display_add_container.grid_columnconfigure(1, weight=1)

        #   дисплей цвета
        self.lp_pallet_display = PalletDisplayFrame(self.lp_display_add_container, self.event_bus, _is_last=True)
        self.lp_pallet_display.grid(row=0, column=0, padx=(0, 0), pady=(0, 0), sticky="nsew")

        #   кнопка добавления
        self.lp_pallet_add = PalletAddButton(self.lp_display_add_container, self.event_bus, _is_last=True)
        self.lp_pallet_add.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky="")

        # MAIN ZONE

        self.editor_use_zone = ImageRenderer(self, self.event_bus, _is_last=True)
        self.editor_use_zone.grid(row=1, column=1, sticky="nswe")
        self.tool_manager.add_use_zone("editor", self.editor_use_zone)


        # RIGHT panel setup
        self.right_panel = CustomPanel(self, self.event_bus, _is_last=True)
        self.right_panel.grid(row=1, column=2, sticky='nse')
        #   3 rows x 1 columns
        self.right_panel.grid_rowconfigure(0, weight=0)
        self.right_panel.grid_rowconfigure(1, weight=0)
        self.right_panel.grid_rowconfigure(2, weight=0)
        self.right_panel.grid_columnconfigure(0, weight=1)

        #   панель инструментов
        self.rp_tool_radio_button_frame = ToolRadioButtonFrame(self.right_panel, self.event_bus, _is_last=True)
        self.rp_tool_radio_button_frame.grid(row=0, column=0, padx=(10, 10), pady=(10, 0), sticky="nsew")
        self.right_panel.grid_rowconfigure(0, minsize=200)

        #   add tools to the tool_panel
        for _tool_name in self.tools:
            self.rp_tool_radio_button_frame.add_tool(_tool_name)

        # панель параметров кластеризации
        self.rp_clustering_frame = ContainerPanel(self.right_panel, self.event_bus, _is_last=True)
        self.rp_clustering_frame.grid(row=1, column=0, padx=(10, 10), pady=(30, 0), sticky="nsew")

        self.rp_blur_slider = BlurSlider(self.rp_clustering_frame, self.event_bus, _is_last=True)
        self.rp_blur_slider.grid(row=0, column=0, padx=(0, 0), pady=(30, 0), sticky="")

        self.rp_clustering_settings_frame = ContainerPanel(self.rp_clustering_frame, self.event_bus, _is_last=True)
        self.rp_clustering_settings_frame.grid(row=1, column=0, padx=(10, 10), pady=(30, 0), sticky="nsew")

        self.rp_count_clusters_entry = CountClustersEntry(self.rp_clustering_settings_frame, self.event_bus, _is_last=True, width=30, height=15)
        self.rp_count_clusters_entry.grid(row=0, column=1, padx=(0, 0), pady=(0, 0), sticky="")

        self.rp_pallet_clusters_centers_frame = PalletClustersCentersFrame(self.rp_clustering_frame, self.event_bus, _is_last=True)
        self.rp_pallet_clusters_centers_frame.grid(row=2, column=0, padx=(0, 0), pady=(10, 0), sticky="nsew")
        self.rp_clustering_frame.grid_rowconfigure(2, minsize=200)

        self.rp_cluster_button = ClusterButton(self.rp_clustering_frame, self.event_bus, _is_last=True)
        self.rp_cluster_button.grid(row=3, column=0, padx=(5, 0), pady=(5, 0), sticky='e')



        # self.cluster_manager = ClusterManager(
        #     event_bus=self.event_bus,
        #     editor_renderer=self.editor_use_zone,
        #     clusters_frame=self.rp_pallet_clusters_centers_frame,
        #     count_entry=self.rp_count_clusters_entry
        # )

        # RENDER ZONE
        self.render_use_zone = ImageRenderer(self.right_panel, self.event_bus, _is_last=True, width=240, height=240)
        self.render_use_zone.grid(row=2, column=0, padx=(10, 10), pady=(10, 0), sticky="")
        self.tool_manager.add_use_zone("render", self.render_use_zone)
        self.cluster_manager = ClusterManager(self.event_bus, self.editor_use_zone, self.render_use_zone, self.rp_pallet_clusters_centers_frame, self.rp_count_clusters_entry)






