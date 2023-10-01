import sys
from PyQt5 import QtGui
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
from PyQt5.QtGui import QIcon
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QDir, Qt, QUrl
from pyqtgraph import InfiniteLine, TextItem
from PyQt5.QtGui import QKeyEvent


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        print("initUI...")

        self.statusBar()

        openFile = QAction(QIcon("open.png"), "Open", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Open New File")
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(openFile)

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

    new_roi_start_line: InfiniteLine = None
    new_roi_start_text: TextItem = None

    new_roi_end_line: InfiniteLine = None
    new_roi_end_text: TextItem = None

    def plot_data(self):
        if self.plot_widget:
            self.main_layout.removeWidget(self.plot_widget)

        self.plot_widget = PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
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
        self.plot_widget_progress_text = TextItem(text="Video Sync", color="#eb34d5")
        self.plot_widget_progress_text.setPos(self.plot_widget_data_start_timestamp, 0)

        self.plot_widget.addItem(self.plot_widget_progress_line)
        self.plot_widget.addItem(self.plot_widget_progress_text)

        self.plot_widget.scene().sigMouseClicked.connect(self.mouse_clicked)

        self.plot_widget.showGrid(x=True, y=False)
        # self.setCentralWidget(self.plot_widget)
        self.main_layout.addWidget(self.plot_widget)

    def mouse_clicked(self, evt):
        print(evt)

    def update_plot_progress(self, position):
        self.current_progress = self.plot_widget_data_start_timestamp + (
            position / 1000
        )
        self.plot_widget_progress_line.setPos(self.current_progress)
        self.plot_widget_progress_text.setPos(self.current_progress, 0)

    # TODO: The code of onRoiStartPressed and onRoiStopPressed overlaps a lot and needs refactoring.

    def onRoiStartPressed(self):
        # print("onRoiStartPressed...")

        if self.new_roi_start_line is None:
            print("Create new ROI start...")
            self.new_roi_start_line = InfiniteLine(
                pos=(self.current_progress, 0), angle=90, pen="#FFFFFF"
            )
            self.new_roi_start_text = TextItem("ROI Start", color="#FFFFFF")
            self.new_roi_start_text.setPos(self.current_progress, -5)

            self.plot_widget.addItem(self.new_roi_start_line)
            self.plot_widget.addItem(self.new_roi_start_text)
        elif self.new_roi_start_line.getXPos() == self.current_progress:
            print("Remove new ROI start...")
            self.plot_widget.removeItem(self.new_roi_start_line)
            self.plot_widget.removeItem(self.new_roi_start_text)
            self.new_roi_start_line = None
            self.new_roi_start_text = None
        else:
            print("Update ROI start position...")
            self.new_roi_start_line.setPos(self.current_progress)
            self.new_roi_start_text.setPos(self.current_progress, -5)

        self.validateRoiPosition()

    def onRoiStopPressed(self):
        # print("onRoiStopPressed...")

        if self.new_roi_end_line is None:
            print("Create new ROI end...")
            self.new_roi_end_line = InfiniteLine(
                pos=(self.current_progress, 0), angle=90, pen="#FFFFFF"
            )
            self.new_roi_end_text = TextItem("ROI End", color="#FFFFFF")
            self.new_roi_end_text.setPos(self.current_progress, -10)

            self.plot_widget.addItem(self.new_roi_end_line)
            self.plot_widget.addItem(self.new_roi_end_text)
        elif self.new_roi_end_line.getXPos() == self.current_progress:
            print("Remove new ROI end...")
            self.plot_widget.removeItem(self.new_roi_end_line)
            self.plot_widget.removeItem(self.new_roi_end_text)
            self.new_roi_end_line = None
            self.new_roi_end_text = None
        else:
            print("Update ROI end position...")
            self.new_roi_end_line.setPos(self.current_progress)
            self.new_roi_end_text.setPos(self.current_progress, -10)

        self.validateRoiPosition()

    def onMarkPressed(self):
        print("onMarkPressed...")

    def validateRoiPosition(self):
        if (
            self.new_roi_start_line
            and self.new_roi_end_line
            and self.new_roi_end_line.getXPos() <= self.new_roi_start_line.getXPos()
        ):
            QMessageBox.about(
                self, "Warning", "ROI End time cannot be earlier than ROI Start time."
            )
            self.plot_widget.removeItem(self.new_roi_start_line)
            self.plot_widget.removeItem(self.new_roi_start_text)
            self.plot_widget.removeItem(self.new_roi_end_line)
            self.plot_widget.removeItem(self.new_roi_end_text)
            self.new_roi_start_line = None
            self.new_roi_start_text = None
            self.new_roi_end_line = None
            self.new_roi_end_text = None

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
