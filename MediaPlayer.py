from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaContent

from util import log_method_call


class MediaPlayer:
    def __init__(self, style, main_window, position_changed_callback) -> None:
        self.style = style
        self.main_window = main_window
        self.position_changed_callback = position_changed_callback
        # self.createViewPlayer()

    @log_method_call
    def create_player_widget(self) -> QWidget:
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setNotifyInterval(50)

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

        # Create a widget for window contents
        wid = QWidget(self.main_window)

        self.openButton = QPushButton("Open")
        self.openButton.clicked.connect(self.open_video_file_dialog)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.currentTimeLabel)
        controlLayout.addWidget(self.openButton)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        return wid

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

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
        error_message = "QMediaPlayerError(" + self.mediaPlayer.errorString() + ")"
        QMessageBox.critical(self.main_window, "Error", error_message)

    def set_media(self, media_content):
        self.mediaPlayer.setMedia(media_content)

    def set_play_button_enabled(self, enabled):
        self.playButton.setEnabled(enabled)

    def set_position(self, position):
        if self.playButton.isEnabled():
            self.mediaPlayer.setPosition(position)

    def open_video_file(self, fileName: str):
        self.set_media(QMediaContent(QUrl.fromLocalFile(fileName)))
        self.set_play_button_enabled(True)

    def open_video_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self.main_window)

        selected_file, _ = file_dialog.getOpenFileName(
            self.main_window,
            "Open Video File",
            "",
            "MP4 Files (*.mp4)",
            options=options,
        )

        if selected_file:
            self.open_video_file(selected_file)
