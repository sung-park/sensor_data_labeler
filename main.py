import sys
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
)
from PyQt5.QtGui import QIcon
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg

from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QDir, Qt, QUrl


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

        # Create new action
        # openAction = QAction(QIcon("open.png"), "&Open", self)
        # openAction.setShortcut("Ctrl+O")
        # openAction.setStatusTip("Open movie")
        # openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(self.exitCall)

        # Create menu bar and add action
        # menuBar = self.menuBar()
        # fileMenu = menuBar.addMenu("&File")

        # fileMenu.addAction(newAction)
        # fileMenu.addAction(openAction)
        # fileMenu.addAction(exitAction)

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
        self.positionSlider.setValue(position)

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

    def open_video_file(self, fileName: str):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
        self.playButton.setEnabled(True)

    # def openFile(self):
    #     fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie", QDir.homePath())

    #     if fileName != "":
    #         self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
    #         self.playButton.setEnabled(True)

    def plot_data(self):
        self.plot_widget = PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
        self.plot_widget.setLabel("left", "acc (x:red, y:green, z:blue)")
        self.plot_widget.setLabel("bottom", "time")

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

        self.plot_widget.showGrid(x=True, y=False)
        # self.setCentralWidget(self.plot_widget)
        self.main_layout.addWidget(self.plot_widget)


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
