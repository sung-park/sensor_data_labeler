from datetime import datetime
import json
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QWidget,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QTextBrowser,
)
from PyQt5.QtGui import QIcon, QDesktopServices
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtCore import QDir, Qt, QUrl
from pyqtgraph import InfiniteLine, TextItem
from PyQt5.QtGui import QKeyEvent
from AnnotationManager import AnnotationManager
from AnnotationRoi import AnnotationRoi

from LineInfoPair import LineInfoPair
from PyQt5.QtGui import QMouseEvent

from MediaPlayer import MediaPlayer
from MediaPlayersManager import MediaPlayersManager
from PopupWindow import PopupWindow
from util import log_method_call


class MyApp(QMainWindow):
    media_players_manager: MediaPlayersManager = None
    annotation_manager = AnnotationManager()

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        print("initUI...")

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        open_csv_file = QAction(QIcon("open.png"), "Open CSV file", self)
        # open_csv_file.setShortcut("Ctrl+O")
        open_csv_file.setStatusTip("Open CSV file")
        open_csv_file.triggered.connect(self.open_new_file_dialog)

        save_annotation_file = QAction(
            QIcon("open.png"), "Save annotation as CSV", self
        )
        # save_annotation_file.setShortcut("Ctrl+S")
        save_annotation_file.setStatusTip("Save annotation as CSV")
        save_annotation_file.triggered.connect(self.save_annotation_file_dialog)

        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(open_csv_file)
        fileMenu.addAction(save_annotation_file)

        keyboard_shortcuts_reference = QAction(
            QIcon("open.png"), "Keyboard Shortcuts Reference", self
        )
        keyboard_shortcuts_reference.triggered.connect(
            self.open_keyboard_shortcuts_reference
        )

        helpMenu = menubar.addMenu("&Help")
        helpMenu.addAction(keyboard_shortcuts_reference)

        self.setWindowTitle("PX Sensor Data Labeler")
        self.setGeometry(300, 300, 1536, 768)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout()
        central_widget.setLayout(self.main_layout)

        self.media_players_manager = MediaPlayersManager(
            self.style(),
            self.main_layout,
            self,
            self.update_plot_progress,
        )

        self.show()

    def open_keyboard_shortcuts_reference(self):
        url = QUrl(
            "https://github.com/sung-park/sensor_data_labeler/blob/main/SHORTCUTS_REF.md"
        )
        QDesktopServices.openUrl(url)

    def save_annotation_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "CSV Files (*.csv)", options=options
        )

        if file_name:
            print(file_name)
            self.annotation_manager.save_to_csv(file_name)

            csv_data_dialog = QDialog(self)
            csv_data_dialog.setWindowTitle("CSV Data")
            csv_data_dialog.setGeometry(400, 400, 640, 240)
            csv_data_text_browser = QTextBrowser(csv_data_dialog)
            csv_data_text_browser.setMinimumSize(640, 240)

            with open(file_name, "r") as file:
                lines = file.readlines()
                data = "".join(lines[:5])

            csv_data_text_browser.setPlainText(data)
            csv_data_dialog.adjustSize()
            csv_data_dialog.setWindowTitle("CSV file has been saved successfully.")
            csv_data_dialog.exec_()

    def open_new_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.HideNameFilterDetails
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV file",
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
        self.sensor_df = pd.read_csv(csv_filename, sep=",", header=0)

        column_names = [col.strip() for col in self.sensor_df.columns]
        column_names_str = ", ".join(column_names)
        print("CSV Columns:", column_names_str)

        self.x_data = self.sensor_df["timestamp"] / 1000.0
        # print(self.x_data)
        self.y_acc_x_data = self.sensor_df["acc_x"]
        self.y_acc_y_data = self.sensor_df["acc_y"]
        self.y_acc_z_data = self.sensor_df["acc_z"]

        self.plot_data()
        self.media_players_manager.open_video_file(0, video_filename)
        # self.media_player.open_video_file(video_filename)

        # Trick to display the first frame of a video
        self.media_players_manager.play()
        self.media_players_manager.play()

    plot_widget: PlotWidget = None

    roi_start = LineInfoPair("ROI Start")
    roi_end = LineInfoPair("ROI End")

    def plot_data(self):
        if self.plot_widget:
            self.main_layout.removeWidget(self.plot_widget)

        self.plot_widget = PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
        self.plot_widget.setMenuEnabled(False)

        self.roi_start.set_plot_widget(self.plot_widget)
        self.roi_end.set_plot_widget(self.plot_widget)

        self.plot_widget.setLabel("left", "Acc (X:Red, Y:Green, Z:Blue)")
        self.plot_widget.setLabel("bottom", "Time")

        self.plot_widget.plot(self.x_data, self.y_acc_x_data, pen="r")
        self.plot_widget.plot(self.x_data, self.y_acc_y_data, pen="g")
        self.plot_widget.plot(self.x_data, self.y_acc_z_data, pen="b")

        # Limit zooming out of the data area
        view_box = self.plot_widget.getViewBox()
        # print(self.x_data.min())
        # print(self.x_data.max())
        view_box.setXRange(self.x_data.min(), self.x_data.max())
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
            pos=(self.plot_widget_data_start_timestamp, 0), angle=90, pen="#eb34d5"
        )
        y_min, y_max = self.plot_widget.getAxis("left").range
        self.plot_widget_progress_text = TextItem(text="Video Sync", color="#eb34d5")
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

        datetime_obj = datetime.fromtimestamp(self.current_progress)
        formatted_datetime = datetime_obj.strftime("%H:%M:%S.%f")[
            :-3
        ] + datetime_obj.strftime(" %Y-%m-%d")
        self.plot_widget_progress_text.setText(formatted_datetime)

    @log_method_call
    def on_roi_start_pressed(self):
        if not self.roi_start.is_marked():
            self.roi_start.mark(self.current_progress)
        elif self.roi_start.getXPos() == self.current_progress:
            self.roi_start.clear()
        else:
            self.roi_start.set_pos(self.current_progress)
        self.validate_roi_position()

    @log_method_call
    def on_roi_end_pressed(self):
        if not self.roi_end.is_marked():
            self.roi_end.mark(self.current_progress)
        elif self.roi_end.getXPos() == self.current_progress:
            self.roi_end.clear()
        else:
            self.roi_end.set_pos(self.current_progress)
        self.validate_roi_position()

    def get_tags(self):
        with open("tags.json", "r") as file:
            config_data = json.load(file)
            tag_data = config_data.get("tags", [])
            return [tag["name"] for tag in config_data.get("tags", [])]

    @log_method_call
    def on_mark_pressed(self):
        items = self.get_tags()

        popup = PopupWindow(items)
        result = popup.exec_()

        if result == QDialog.Accepted:
            selected_item = popup.selected_item
            print("Selected item:", selected_item)
        else:
            return

        self.annotation_manager.add(
            AnnotationRoi(
                self.plot_widget,
                self.roi_start.getXPos(),
                self.roi_end.getXPos(),
                selected_item,
            )
        )

        self.roi_start.clear()
        self.roi_end.clear()

    def validate_roi_position(self):
        if (
            self.roi_start.is_marked()
            and self.roi_end.is_marked()
            and self.roi_end.getXPos() <= self.roi_start.getXPos()
        ):
            QMessageBox.about(
                self, "Warning", "ROI End time cannot be earlier than ROI Start time."
            )
            self.roi_start.clear()
            self.roi_end.clear()

    def keyPressEvent(self, key_event: QKeyEvent) -> None:
        pass
        # if key_event.key() == Qt.Key.Key_S and not key_event.isAutoRepeat():
        #     print("S pressed")

        # if key_event.key() == Qt.Key.Key_E and not key_event.isAutoRepeat():
        #     print("E pressed")

    def keyReleaseEvent(self, key_event: QKeyEvent) -> None:
        if key_event.key() == Qt.Key.Key_S and not key_event.isAutoRepeat():
            self.on_roi_start_pressed()
            # print("S released")

        if key_event.key() == Qt.Key.Key_E and not key_event.isAutoRepeat():
            self.on_roi_end_pressed()
            # print("E released")

        if key_event.key() == Qt.Key.Key_M and not key_event.isAutoRepeat():
            self.on_mark_pressed()

        if key_event.key() == Qt.Key.Key_Space and not key_event.isAutoRepeat():
            # self.media_player.play()
            self.media_players_manager.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
