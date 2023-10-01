from datetime import datetime
import sys
from PyQt5 import QtGui
import PyQt5
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QWidget,
    QPushButton,
    QStyle,
    QSlider,
    QLabel,
    QSizePolicy,
    QHBoxLayout,
    QVBoxLayout,
    QMessageBox,
)
from PyQt5.QtGui import QIcon, QColor, QDesktopServices
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QDir, Qt, QUrl
from pyqtgraph import InfiniteLine, TextItem
from PyQt5.QtGui import QKeyEvent

from LineInfoPair import LineInfoPair
from PyQt5.QtGui import QMouseEvent


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        print("initUI...")

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        openFile = QAction(QIcon("open.png"), "Open", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Open New File")
        openFile.triggered.connect(self.showDialog)

        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(openFile)

        keyboard_shortcuts_reference = QAction(
            QIcon("open.png"), "Keyboard Shortcuts Reference", self
        )
        keyboard_shortcuts_reference.triggered.connect(
            self.open_keyboard_shortcuts_reference
        )

        helpMenu = menubar.addMenu("&Help")
        helpMenu.addAction(keyboard_shortcuts_reference)

        self.setWindowTitle("PX Sensor Data Labeler")
        self.setGeometry(300, 300, 1536, 576)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout()
        central_widget.setLayout(self.main_layout)

        self.createViewPlayer()

        self.show()

    def createViewPlayer(self):
        print("createViewPlayer...")

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.currentTimeLabel = QLabel()
        self.currentTimeLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Create exit action
        exitAction = QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(self.exitCall)

        # Create a widget for window contents
        wid = QWidget(self)
        self.main_layout.addWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)
        layout.addWidget(self.currentTimeLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def exitCall(self):
        sys.exit(app.exec_())

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        seconds = position / 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        timeStr = "{:02}:{:02}:{:02}.{:03}".format(
            int(hours), int(minutes), int(seconds), int(position % 1000)
        )
        self.currentTimeLabel.setText(timeStr)

        self.positionSlider.setValue(position)

        self.update_plot_progress(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def open_keyboard_shortcuts_reference(self):
        url = QUrl(
            "https://github.com/sung-park/sensor_data_labeler/blob/main/SHORTCUTS_REF.md"
        )
        QDesktopServices.openUrl(url)

    def showDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.ExistingFiles
        options |= QFileDialog.HideNameFilterDetails
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV file",
            "./",
            "CSV Files (*.csv);;All Files (*)",
            options=options,
        )
        if not fname:
            print("ERROR: invalid CSV filename")
            return

        csv_filename = fname
        video_filename = csv_filename.replace(".csv", ".mp4")

        print("Input CSV filename: ", csv_filename)
        print("Input MP4 filename: ", video_filename)
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
        self.open_video_file(video_filename)

        # Trick to display the first frame of a video
        self.play()
        self.play()

    def open_video_file(self, fileName: str):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
        self.playButton.setEnabled(True)

    plot_widget: PlotWidget = None

    roi_start = LineInfoPair("ROI Start")
    roi_end = LineInfoPair("ROI End")

    def plot_data(self):
        if self.plot_widget:
            self.main_layout.removeWidget(self.plot_widget)

        self.plot_widget = PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
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

        self.mediaPlayer.setPosition(int(delta * 1000.0))

    def update_plot_progress(self, position):
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

    def onRoiStartPressed(self):
        if not self.roi_start.is_marked():
            self.roi_start.mark(self.current_progress)
        elif self.roi_start.getXPos() == self.current_progress:
            self.roi_start.clear()
        else:
            self.roi_start.set_pos(self.current_progress)
        self.validate_roi_position()

    def onRoiStopPressed(self):
        if not self.roi_end.is_marked():
            self.roi_end.mark(self.current_progress)
        elif self.roi_end.getXPos() == self.current_progress:
            self.roi_end.clear()
        else:
            self.roi_end.set_pos(self.current_progress)
        self.validate_roi_position()

    def onMarkPressed(self):
        print("onMarkPressed...")

        # y_min: -22.847815470229374 y_max 24.77754347022937
        y_min, y_max = self.plot_widget.getAxis("left").range

        roi = pg.RectROI(
            [self.roi_start.getXPos(), y_min],
            [
                self.roi_end.getXPos() - self.roi_start.getXPos(),
                10,
            ],
            pen="y",
            movable=False,
            resizable=False,
            rotatable=False,
        )
        roi.setZValue(10)

        self.plot_widget.addItem(roi)

        text_item = pg.TextItem(text="Annotated", anchor=(0.5, 0.5), color="y")
        roi_rect = roi.boundingRect()
        text_item.setPos(
            self.roi_start.getXPos() + roi_rect.center().x(),
            y_min + roi_rect.center().y(),
        )
        self.plot_widget.addItem(text_item)

        roi.setAcceptedMouseButtons(PyQt5.QtCore.Qt.MouseButton.LeftButton)
        roi.sigClicked.connect(self.roi_mouse_clicked)

    def roi_mouse_clicked(self, evt):
        print(evt)

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
            self.onRoiStartPressed()
            # print("S released")

        if key_event.key() == Qt.Key.Key_E and not key_event.isAutoRepeat():
            self.onRoiStopPressed()
            # print("E released")

        if key_event.key() == Qt.Key.Key_M and not key_event.isAutoRepeat():
            self.onMarkPressed()

        if key_event.key() == Qt.Key.Key_Space and not key_event.isAutoRepeat():
            self.play()


class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 800, 600)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.set_position)

        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.slider)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
