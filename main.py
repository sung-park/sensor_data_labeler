import csv
from datetime import datetime
import json
import os
import sys
from typing import List
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDesktopServices
import pandas as pd
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from PyQt5.QtCore import QUrl
from pyqtgraph import InfiniteLine, TextItem
from AnnotationManager import AnnotationManager
from AnnotationRoi import AnnotationRoi

from PyQt5.QtGui import QMouseEvent

from MediaPlayersManager import MediaPlayersManager
from MyPlotWidget import MyPlotWidget
from StatsDialog import StatsDialog
from TagsManager import TagsManager
from config import *


class MyApp(QMainWindow):
    media_players_manager: MediaPlayersManager = None
    annotation_manager = AnnotationManager()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        print("initUI...")

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        menubar.addMenu(self.create_file_menu())
        menubar.addMenu(self.create_view_menu())
        menubar.addMenu(self.create_tool_menu())
        menubar.addMenu(self.create_help_menu())

        self.setWindowTitle(f"PX Sensor Data Labeler v{VERSION}")
        self.setGeometry(0, 0, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        self.root_layout = QVBoxLayout()
        self.main_layout = QHBoxLayout()
        self.note_layout = QVBoxLayout()

        self.root_layout.addLayout(self.main_layout)
        self.root_layout.addLayout(self.note_layout)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setLayout(self.root_layout)

        self.media_players_manager = MediaPlayersManager(
            self.style(),
            self.main_layout,
            self,
            self.update_plot_progress,
        )

        self.add_note_widget()

        self.show()

    def add_note_widget(self):
        note_label = QLabel("Note")
        note_label.setMaximumHeight(note_label.sizeHint().height())

        self.note_text_edit = QTextEdit()
        self.note_text_edit.setFixedHeight(
            5 * self.note_text_edit.fontMetrics().lineSpacing()
        )
        self.note_text_edit.setPlaceholderText(
            "(Sean) The screen is too dark for me to see, so sensor labeling is impossible."
        )
        self.note_layout.addWidget(note_label)
        self.note_layout.addWidget(self.note_text_edit)

    def create_help_menu(self) -> QMenu:
        menu = QMenu("&Help", self)
        action = QAction("Keyboard Shortcuts Reference", self)
        action.triggered.connect(self.open_keyboard_shortcuts_reference)
        menu.addAction(action)

        return menu

    def create_file_menu(self):
        menu = QMenu("&File", self)

        actions = [
            ("Open CSV Data File", self.open_data_file),
            ("Save Annotation File", self.save_annotation_file),
            ("Export CSV Data File With Annotation", self.export_csv_with_annotation),
        ]

        for action_text, action_function in actions:
            action = QAction(action_text, self, triggered=action_function)
            menu.addAction(action)

        return menu

    def create_tool_menu(self):
        menu = QMenu("&Tool", self)

        actions = [
            ("Check Annotation Statistics", self.check_annotation_statistics),
        ]

        for action_text, action_function in actions:
            action = QAction(action_text, self, triggered=action_function)
            menu.addAction(action)

        return menu

    def create_view_menu(self) -> QMenu:
        view_modes = ["Single", "Even", "Portrait", "Landscape"]
        menu = QMenu("&View Mode", self)

        action_group = QActionGroup(menu)
        action_group.setExclusive(True)
        action_group.triggered.connect(self.on_view_mode_changed)

        for view_mode in view_modes:
            action = QAction(
                view_mode,
                menu,
                checkable=True,
                checked=view_mode == view_modes[0],
            )
            menu.addAction(action)
            action_group.addAction(action)

        return menu

    def check_annotation_statistics(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly

        folder_path = QFileDialog.getExistingDirectory(
            None, "Select Folder", "", options=options
        )

        if folder_path:
            print("Selected folder path:", folder_path)
            ann_files = self.find_ann_files(folder_path)

            total_behavior_durations = {}

            for ann_file in ann_files:
                behavior_durations = self.annotation_manager.calculate_statistics(
                    ann_file
                )
                for behavior, duration in behavior_durations.items():
                    if behavior in total_behavior_durations:
                        total_behavior_durations[behavior] += duration
                    else:
                        total_behavior_durations[behavior] = duration

            stats_popup = StatsDialog(total_behavior_durations, self)
            stats_popup.exec_()

    def find_ann_files(self, root_folder):
        ann_files = []
        for folder, subfolders, files in os.walk(root_folder):
            for file in files:
                if file.endswith(".ann"):
                    ann_files.append(os.path.join(folder, file))
        return ann_files

    def on_view_mode_changed(self, action):
        if "Single" in action.text():
            self.media_players_manager.set_view_mode_single()
        elif "Even" in action.text():
            self.media_players_manager.set_view_mode_even()
        elif "Portrait" in action.text():
            self.media_players_manager.set_view_mode_portrait()
        elif "Landscape" in action.text():
            self.media_players_manager.set_view_mode_landscape()

    def open_keyboard_shortcuts_reference(self):
        url = QUrl(
            "https://github.com/sung-park/sensor_data_labeler/blob/main/SHORTCUTS_REF.md"
        )
        QDesktopServices.openUrl(url)

    def export_csv_with_annotation(self):
        sensor_data_df = pd.read_csv(self.sensor_data_csv_filename, encoding="UTF8")

        with open(
            self.sensor_data_csv_filename.replace(".csv", ".ann"), "r", encoding="utf8"
        ) as file:
            data = json.load(file)
        annotations = data["annotations"]
        annotation_df = pd.DataFrame(annotations)

        for index, annotation_row in annotation_df.iterrows():
            start_timestamp = annotation_row["start_timestamp"]
            end_timestamp = annotation_row["end_timestamp"]
            behavior: str = annotation_row["behavior"]

            words = behavior.split("::")
            tag_type = words[0]
            tag_name = words[1]

            mask = (sensor_data_df["timestamp"] >= start_timestamp) & (
                sensor_data_df["timestamp"] <= end_timestamp
            )

            if tag_type not in sensor_data_df.columns:
                sensor_data_df[tag_type] = "None"
                sensor_data_df[tag_type] = sensor_data_df[tag_type].astype(str)
            sensor_data_df.loc[mask, tag_type] = tag_name

        for tag_type in TagsManager().types:
            if tag_type not in sensor_data_df:
                sensor_data_df[tag_type] = "None"
            # sensor_data_df[tag_type].replace("", "None", inplace=True)
            sensor_data_df.loc[sensor_data_df[tag_type].isnull(), tag_type] = "None"

        directory, file_name = os.path.split(self.sensor_data_csv_filename)
        file_name_without_extension, extension = os.path.splitext(file_name)
        new_file_name = file_name_without_extension + "_labeled" + extension
        new_path = os.path.join(directory, new_file_name)
        sensor_data_df.to_csv(new_path, index=False)

        QMessageBox.information(
            self,
            "Information",
            f"The original data and annotations have been successfully integrated and saved!\n"
            + new_path,
        )

    def load_annotation_file(self, filename):
        self.annotation_manager.clear()
        offset, note = self.annotation_manager.load_from_ann(filename, self.plot_widget)
        if offset is not None:
            print(f"Change offset to {offset} by ANN meta")
            self.media_players_manager.change_offset(offset)
        self.note_text_edit.setText(note)

    def save_annotation_file(self):
        if not self.sensor_data_csv_filename:
            print("ERROR: A sensor data file has not yet been opened.")
            return

        suggested_annotation_filename = self.sensor_data_csv_filename.replace(
            ".csv", ".ann"
        )
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotation File",
            suggested_annotation_filename,
            "ANN Files(*.ann)",
            options=options,
        )

        if file_name:
            print(file_name)
            self.annotation_manager.save_to_ann(
                file_name,
                self.x_data.min(),
                self.x_data.max(),
                self.media_players_manager.get_offset(),
                self.note_text_edit.toPlainText(),
            )

            ann_data_dialog = QDialog(self)
            ann_data_dialog.setWindowTitle(file_name)
            ann_data_dialog.setGeometry(400, 400, 640, 240)

            ann_data_text_browser = QTextBrowser(ann_data_dialog)
            ann_data_text_browser.setMinimumSize(640, 240)
            ann_data_text_browser.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )

            with open(file_name, "r", encoding="utf-8") as file:
                lines = file.readlines()
                data = "".join(lines)

            ann_data_text_browser.setPlainText(data)
            ann_data_dialog.adjustSize()
            ann_data_dialog.exec_()

    sensor_data_csv_filename = None
    sensor_data_json_filename = None

    def open_data_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.HideNameFilterDetails
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV Data File",
            "",
            "CSV File(*.csv);;",
            options=options,
        )
        if not fname:
            print("ERROR: invalid CSV filename")
            return

        csv_filename = fname
        video_filename = csv_filename.replace(".csv", ".mp4")

        print("Input CSV filename:", csv_filename)
        print("Input MP4 filename:", video_filename)

        self.parse_sensor_data(csv_filename)

        self.plot_data()

        self.open_video(video_filename)

        self.apply_offset_if_needed(csv_filename)
        self.sensor_data_csv_filename = csv_filename

        self.note_text_edit.clear()

        self.ask_and_open_annotation_file(
            self.sensor_data_csv_filename.replace("csv", "ann")
        )

    def apply_offset_if_needed(self, csv_filename):
        self.media_players_manager.change_offset(0)

        self.sensor_data_json_filename = csv_filename.replace(".csv", ".json")
        if os.path.isfile(self.sensor_data_json_filename):
            with open(
                self.sensor_data_json_filename, "r", encoding="utf-8"
            ) as json_file:
                try:
                    json_data = json.load(json_file)

                    video_start_time_ms = json_data.get("videoStartTimeMs")
                    sensor_start_time_ms = json_data.get("sensorStartTimeMs")

                    self.media_players_manager.change_offset(
                        sensor_start_time_ms - video_start_time_ms
                    )
                except json.JSONDecodeError:
                    print("Unable to parse the JSON file.")

    def open_video(self, video_filename):
        self.media_players_manager.open_video_file(0, video_filename)
        # self.media_player.open_video_file(video_filename)

        # Trick to display the first frame of a video
        self.media_players_manager.play()
        self.media_players_manager.play()

    def parse_sensor_data(self, csv_filename):
        self.sensor_df = pd.read_csv(csv_filename, sep=",", header=0)
        column_names = [col.strip() for col in self.sensor_df.columns]
        column_names_str = ", ".join(column_names)
        print("CSV Columns:", column_names_str)

        self.x_data = self.sensor_df["timestamp"] / 1000.0
        self.y_acc_x_data = self.sensor_df["acc_x"]
        self.y_acc_y_data = self.sensor_df["acc_y"]
        self.y_acc_z_data = self.sensor_df["acc_z"]
        self.y_data_min = min(
            self.y_acc_x_data.min(), self.y_acc_y_data.min(), self.y_acc_z_data.min()
        )
        self.y_data_max = max(
            self.y_acc_x_data.max(), self.y_acc_y_data.max(), self.y_acc_z_data.max()
        )

    def ask_and_open_annotation_file(self, filename):
        if os.path.exists(filename):
            reply = QMessageBox.question(
                self,
                "Reading Annotation File",
                "An annotation file (.ann) with a name matching the CSV file exists. Would you like to view it together?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.load_annotation_file(filename)

    plot_widget: MyPlotWidget = None

    def get_current_progress(self) -> int:
        return self.current_progress

    def update_video_progress(self, position):
        delta = position - self.x_data.min()
        if delta < 0:
            delta = 0.0

        self.media_players_manager.set_position(int(delta * 1000.0))

    def plot_data(self):
        if self.plot_widget:
            self.main_layout.removeWidget(self.plot_widget)

        self.plot_widget = MyPlotWidget(
            axisItems={"bottom": pg.DateAxisItem()},
            create_roi_cb=self.create_roi,
            get_current_progress_cb=self.get_current_progress,
            change_video_play_state_cb=self.change_video_play_state,
            update_video_progress=self.update_video_progress,
        )

        self.plot_widget.setBackground(PLOT_WIDGET_BG_COLOR)

        self.plot_widget.setMenuEnabled(False)

        self.plot_widget.setLabel("left", "Acc ")
        self.plot_widget.setLabel("bottom", "Time")

        thickness = 1
        self.plot_widget.plot(
            self.x_data,
            self.y_acc_x_data,
            pen={"color": (128, 128, 128), "width": thickness},
        )
        self.plot_widget.plot(
            self.x_data,
            self.y_acc_y_data,
            pen={"color": (0, 0, 128), "width": thickness},
        )
        self.plot_widget.plot(
            self.x_data,
            self.y_acc_z_data,
            pen={"color": (34, 139, 34), "width": thickness},
        )

        # Limit zooming out of the data area
        view_box = self.plot_widget.getViewBox()
        # print(self.x_data.min())
        # print(self.x_data.max())
        view_box.setXRange(self.x_data.min(), self.x_data.max())
        view_box.setYRange(
            self.y_data_min - (self.tags_manager.get_num_of_types() * TAGS_HEIGHT),
            self.y_data_max,
        )
        view_range = view_box.viewRange()
        view_box.setLimits(
            xMin=view_range[0][0],
            xMax=view_range[0][1],
            yMin=view_range[1][0],
            yMax=view_range[1][1],
        )
        self.plot_widget.plotItem.setMouseEnabled(y=False)

        self.plot_widget_data_start_timestamp = self.x_data.min()
        self.plot_widget_progress_line = InfiniteLine(
            pos=(self.plot_widget_data_start_timestamp, 0),
            angle=90,
            pen={"color": PROGRESS_LINE_COLOR, "width": PROGRESS_LINE_WIDTH},
        )
        y_min, y_max = self.plot_widget.getAxis("left").range
        self.plot_widget_progress_text = TextItem(
            text="Video Sync", color=PROGRESS_LINE_COLOR
        )
        # self.plot_widget_progress_text.setPos(y_max - 10, 0)

        self.plot_widget.addItem(self.plot_widget_progress_line)
        self.plot_widget.addItem(self.plot_widget_progress_text)

        self.plot_widget.scene().sigMouseClicked.connect(self.on_plot_widget_clicked)

        self.plot_widget.showGrid(x=True, y=False)
        # self.setCentralWidget(self.plot_widget)
        self.main_layout.addWidget(self.plot_widget)

    def on_plot_widget_clicked(self, event: QMouseEvent):
        mouse_point = self.plot_widget.getPlotItem().vb.mapSceneToView(event.scenePos())
        delta = mouse_point.x() - self.x_data.min()
        if delta < 0:
            delta = 0.0

        # self.media_player.set_position(int(delta * 1000.0))
        self.media_players_manager.set_position(int(delta * 1000.0))

    last_position = -1

    def update_plot_progress(self, position):
        if position == self.last_position:
            return
        self.last_position = position

        self.current_progress = self.plot_widget_data_start_timestamp + (
            position / 1000
        )
        self.plot_widget_progress_line.setPos(self.current_progress)
        y_min, y_max = self.plot_widget.getAxis("left").range
        self.plot_widget_progress_text.setPos(self.current_progress, y_max - 2)

        self.update_plot_widget_x_range_if_needed()

        datetime_obj = datetime.fromtimestamp(self.current_progress)
        formatted_datetime = datetime_obj.strftime("%H:%M:%S.%f")[
            :-3
        ] + datetime_obj.strftime(" %Y-%m-%d")
        self.plot_widget_progress_text.setText(formatted_datetime)

        subtitle_text = ""
        annotations: List[AnnotationRoi] = self.annotation_manager.get_annotations(
            self.current_progress
        )
        subtitle_text = "\n".join(
            annotation.annotation_text.split("::")[2] for annotation in annotations
        )
        self.media_players_manager.set_subtitle_text(subtitle_text)

    tags_manager = TagsManager()

    def update_plot_widget_x_range_if_needed(self):
        x_min, x_max = self.plot_widget.getAxis("bottom").range

        if self.current_progress < x_min or self.current_progress > x_max:
            current_range = x_max - x_min
            new_x_min = self.current_progress - (current_range / 2)
            new_x_max = self.current_progress + (current_range / 2)
            self.plot_widget.setXRange(new_x_min, new_x_max)

    def create_roi(
        self, widget: QWidget, roi_x_start: int, roi_x_end: int, description: str
    ):
        self.annotation_manager.add(
            AnnotationRoi(
                widget,
                roi_x_start,
                roi_x_end,
                description,
            )
        )

    def change_video_play_state(self):
        self.media_players_manager.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
