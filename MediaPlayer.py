from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (
    QAction,
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
from PyQt5.QtCore import Qt
import sys


class MediaPlayer:
    def __init__(
        self, style, main_window, main_layout, position_changed_callback
    ) -> None:
        self.style = style
        self.main_window = main_window
        self.main_layout = main_layout
        self.position_changed_callback = position_changed_callback
        self.createViewPlayer()

    def createViewPlayer(self):
        print("createViewPlayer...")

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        videoWidget = QVideoWidget()

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style.standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.currentTimeLabel = QLabel()
        self.currentTimeLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Create exit action
        exitAction = QAction(QIcon("exit.png"), "&Exit", self.main_window)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(self.exitCall)

        # Create a widget for window contents
        wid = QWidget(self.main_window)
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
            self.playButton.setIcon(self.style.standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style.standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        seconds = position / 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        timeStr = "{:02}:{:02}:{:02}.{:03}".format(
            int(hours), int(minutes), int(seconds), int(position % 1000)
        )
        self.currentTimeLabel.setText(timeStr)

        self.positionSlider.setValue(position)

        # self.update_plot_progress(position)
        self.position_changed_callback(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def set_media(self, media_content):
        self.mediaPlayer.setMedia(media_content)

    def set_play_button_enabled(self, enabled):
        self.playButton.setEnabled(enabled)

    def set_position(self, position):
        self.mediaPlayer.setPosition(position)
