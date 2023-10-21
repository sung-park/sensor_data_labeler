from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaContent

from util import log_method_call


class MediaPlayer:
    def __init__(self, style, main_window, position_changed_callback) -> None:
        self.style = style
        self.main_window = main_window
        self.position_changed_callback = position_changed_callback

    rotation_degree = 0
    video_offset = 0
    subtitle_text = None

    def set_subtitle_text(self, text: str):
        if text == self.subtitle_text:
            return
        self.subtitle_text = text
        self.subtitle_item.setPlainText(text)
        self.update_subtitle_pos()
        self.subtitle_background_rect.setRect(self.subtitle_item.boundingRect())

    @log_method_call
    def create_player_widget(self) -> QWidget:
        # Create a widget for window contents
        wid = QWidget(self.main_window)

        self._scene = QGraphicsScene(wid)
        self._gv = QGraphicsView(self._scene)

        self.subtitle_item = QGraphicsTextItem("")
        self.subtitle_item.setDefaultTextColor(Qt.red)  # 텍스트 색상 설정
        subtitle_item_font = QFont("Arial", 12)
        subtitle_item_font.setBold(True)
        self.subtitle_item.setFont(subtitle_item_font)  # 폰트 및 글꼴 크기 설정
        # self.subtitle_item.setPlainText("New Subtitle Text")

        # Create a QGraphicsRectItem to set the background
        self.subtitle_background_rect = QGraphicsRectItem(
            self.subtitle_item.boundingRect()
        )
        # Set the pen of the background rect to be transparent (no border)
        border_pen = QPen(Qt.NoPen)
        background_color = QColor(255, 255, 255, 128)  # White with 50% transparency
        self.subtitle_background_rect.setPen(border_pen)
        self.subtitle_background_rect.setBrush(background_color)

        # Group the text item and the background rect
        group = QGraphicsItemGroup()
        group.addToGroup(self.subtitle_background_rect)
        group.addToGroup(self.subtitle_item)

        self._videoitem = QGraphicsVideoItem()
        self._scene.addItem(self._videoitem)
        # self._scene.addItem(self.subtitle_item)
        self._scene.addItem(group)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setNotifyInterval(50)

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style.standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.rotateButton = QPushButton()
        self.rotateButton.setEnabled(True)
        self.rotateButton.setIcon(self.style.standardIcon(QStyle.SP_BrowserReload))
        self.rotateButton.clicked.connect(self.rotate)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.currentTimeLabel = QLabel()
        self.currentTimeLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self.openButton = QPushButton("Open")
        self.openButton.clicked.connect(self.open_video_file_dialog)

        self.offsetInput = QLineEdit()
        self.offsetInput.setPlaceholderText("Offset (ms)")
        self.offsetApplyButton = QPushButton("Apply")
        self.offsetInput.setFixedWidth(100)
        self.offsetApplyButton.clicked.connect(self.apply_offset)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.rotateButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.openButton)

        statusLayout = QHBoxLayout()
        statusLayout.addWidget(self.offsetInput)
        statusLayout.addWidget(self.offsetApplyButton)
        statusLayout.addWidget(self.currentTimeLabel)

        layout = QVBoxLayout()
        # layout.addWidget(videoWidget)
        layout.addWidget(self._gv)
        layout.addLayout(controlLayout)
        layout.addLayout(statusLayout)

        # Set widget to contain window contents
        wid.setLayout(layout)

        # self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.setVideoOutput(self._videoitem)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        return wid

    def update_subtitle_pos(self):
        # _scene의 크기 얻기
        scene_rect = self._scene.sceneRect()
        # print(f"scene_rect: {scene_rect}")

        # subtitle_item의 크기 얻기
        subtitle_rect = self.subtitle_item.boundingRect()

        # _scene의 가운데 하단 위치 계산
        x_pos = (scene_rect.width() - subtitle_rect.width()) / 2
        y_pos = (scene_rect.height() - subtitle_rect.height()) / 2

        # subtitle_item의 위치 설정
        self.subtitle_item.setPos(x_pos, y_pos)
        self.subtitle_background_rect.setPos(x_pos, y_pos)

    def apply_offset(self):
        self.video_offset = int(self.offsetInput.text())

    def change_offset(self, video_offset: int):
        self.offsetInput.setText(str(video_offset))
        self.apply_offset()

    def rotate(self):
        self.rotation_degree = self.rotation_degree + 90
        if self.rotation_degree >= 360:
            self.rotation_degree = 0

        # 비디오 아이템의 중심을 회전 중심으로 설정
        self._videoitem.setTransformOriginPoint(self._videoitem.boundingRect().center())

        # video item 회전
        self._videoitem.setRotation(self.rotation_degree)
        self._videoitem.setPos(0, 0)

        # video item을 화면에 맞추기 (비율 유지 및 확장)
        self._gv.fitInView(self._videoitem, Qt.KeepAspectRatio)

        # subtitle 위치 업데이트
        self.update_subtitle_pos()

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

        self.update_subtitle_pos()

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
        self.position_changed_callback(position - self.video_offset)

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
