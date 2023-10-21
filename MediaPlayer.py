from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaContent

from util import log_method_call


class MediaPlayer:
    def __init__(self, style, main_window) -> None:
        self.style = style
        self.main_window = main_window

        self.rotation_degree = 0
        self.video_offset = 0
        self.subtitle_text = None

    def add_position_changed_observer(self, observer):
        self.position_changed_callback = observer

    def set_subtitle_text(self, text: str):
        if text == self.subtitle_text:
            return
        self.subtitle_text = text

        self.subtitle_item.setPlainText(text)
        self.update_subtitle_pos()
        self.subtitle_background_rect.setRect(self.subtitle_item.boundingRect())

    @log_method_call
    def create_player_widget(self) -> QWidget:
        widget = QWidget(self.main_window)

        self.video_scene = QGraphicsScene(widget)
        self.video_item = QGraphicsVideoItem()
        self.video_scene.addItem(self.video_item)
        self.video_scene.addItem(self.create_subtitle_item_group())
        self.video_view = QGraphicsView(self.video_scene)

        self.create_media_player()

        layout = QVBoxLayout()
        layout.addWidget(self.video_view)
        layout.addLayout(self.create_control_layout())
        layout.addLayout(self.create_status_layout())
        widget.setLayout(layout)

        return widget

    def create_media_player(self):
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setNotifyInterval(50)
        self.media_player.setVideoOutput(self.video_item)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handleError)

    def create_status_layout(self):
        self.offset_text_edit = QLineEdit(placeholderText="Offset (ms)")
        self.offset_text_edit.setFixedWidth(100)
        self.offset_text_edit.setValidator(QIntValidator())

        self.offset_apply_button = QPushButton("Apply", clicked=self.apply_offset)
        self.current_time_label = QLabel(
            sizePolicy=QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        )

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.offset_text_edit)
        status_layout.addWidget(self.offset_apply_button)
        status_layout.addWidget(self.current_time_label)

        return status_layout

    def create_control_layout(self):
        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(self.style.standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play)

        self.rotate_button = QPushButton()
        self.rotate_button.setEnabled(True)
        self.rotate_button.setIcon(self.style.standardIcon(QStyle.SP_BrowserReload))
        self.rotate_button.clicked.connect(self.rotate_clicked)
        self.rotate_button.setFocusPolicy(Qt.NoFocus)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.setPosition)

        self.open_video_button = QPushButton("Open")
        self.open_video_button.clicked.connect(self.open_video_dialog)

        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.rotate_button)
        control_layout.addWidget(self.position_slider)
        control_layout.addWidget(self.open_video_button)

        return control_layout

    def create_subtitle_item_group(self):
        self.subtitle_item = QGraphicsTextItem()
        self.subtitle_item.setDefaultTextColor(Qt.red)
        self.subtitle_item.setFont(QFont("Arial", 12, QFont.Bold))

        self.subtitle_background_rect = QGraphicsRectItem(
            self.subtitle_item.boundingRect()
        )
        self.subtitle_background_rect.setPen(QPen(Qt.NoPen))
        self.subtitle_background_rect.setBrush(QColor(255, 255, 255, 128))

        group = QGraphicsItemGroup()
        group.addToGroup(self.subtitle_background_rect)
        group.addToGroup(self.subtitle_item)

        return group

    def update_subtitle_pos(self):
        # Get the scene rectangle and bounding rectangle of the subtitle item
        scene_rect = self.video_scene.sceneRect()
        subtitle_rect = self.subtitle_item.boundingRect()

        # Calculate the x and y positions to center the subtitle
        x_pos = (scene_rect.width() - subtitle_rect.width()) / 2
        y_pos = (scene_rect.height() - subtitle_rect.height()) / 2

        # Set the positions of the subtitle item and the background rectangle
        self.subtitle_item.setPos(x_pos, y_pos)
        self.subtitle_background_rect.setPos(x_pos, y_pos)

    def apply_offset(self):
        self.video_offset = int(self.offset_text_edit.text())

    def change_offset(self, video_offset: int):
        self.offset_text_edit.setText(str(video_offset))
        self.apply_offset()

    def rotate_clicked(self):
        self.rotate_video()

    def rotate_video(self, angle=90):
        # Update the rotation degree and ensure it stays within 0-359 range
        self.rotation_degree = (self.rotation_degree + angle) % 360

        # Set the rotation center at the center of the video item
        self.video_item.setTransformOriginPoint(self.video_item.boundingRect().center())

        # Rotate the video item and reset its position
        self.video_item.setRotation(self.rotation_degree)
        self.video_item.setPos(0, 0)

        self.adjust_video_size_and_subtitle_pos()

    def adjust_video_size_and_subtitle_pos(self):
        # Fit the video item within the view while maintaining its aspect ratio
        self.video_view.fitInView(self.video_item, Qt.KeepAspectRatio)

        # Update the position of subtitles
        self.update_subtitle_pos()

    def play(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def setPosition(self, position):
        self.media_player.setPosition(position)

    def media_state_changed(self, state):
        icon = (
            QStyle.SP_MediaPause
            if self.media_player.state() == QMediaPlayer.PlayingState
            else QStyle.SP_MediaPlay
        )
        self.play_button.setIcon(self.style.standardIcon(icon))

        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.adjust_video_size_and_subtitle_pos()

    def position_changed(self, position):
        seconds = position / 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        timeStr = "{:02}:{:02}:{:02}.{:03}".format(
            int(hours), int(minutes), int(seconds), int(position % 1000)
        )
        self.current_time_label.setText(timeStr)

        self.position_slider.setValue(position)

        if self.position_changed_callback:
            self.position_changed_callback(position - self.video_offset)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def setPosition(self, position):
        self.media_player.setPosition(position)

    def handleError(self):
        self.play_button.setEnabled(False)
        error_message = "QMediaPlayerError(" + self.media_player.errorString() + ")"
        QMessageBox.critical(self.main_window, "Error", error_message)

    def set_media(self, media_content):
        self.media_player.setMedia(media_content)

    def set_play_button_enabled(self, enabled):
        self.play_button.setEnabled(enabled)

    def set_position(self, position):
        if self.play_button.isEnabled():
            self.media_player.setPosition(position)

    def open_video_file(self, fileName: str):
        self.set_media(QMediaContent(QUrl.fromLocalFile(fileName)))
        self.set_play_button_enabled(True)

    def open_video_dialog(self):
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
