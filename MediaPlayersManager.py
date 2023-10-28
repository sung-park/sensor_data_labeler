from typing import List
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *

from MediaPlayer import MediaPlayer
from util import log_method_call


class MediaPlayersManager:
    def __init__(self, style, main_layout, main_window, update_plot_progress) -> None:
        grid_layout = QGridLayout()
        self.media_players: List[MediaPlayer] = []
        self.media_players_widgets: List[QWidget] = []
        for i in range(2):
            for j in range(2):
                media_player = MediaPlayer(
                    style,
                    main_window,
                )
                media_player.add_position_changed_observer(update_plot_progress)
                self.media_players.append(media_player)
                widget = media_player.create_player_widget()
                self.media_players_widgets.append(widget)
                grid_layout.addWidget(widget, i, j)

        self.video_players_widget: QWidget = QWidget(main_window)
        self.video_players_widget.setLayout(grid_layout)

        main_layout.addWidget(self.video_players_widget)

        self.set_view_mode_single()

    @log_method_call
    def open_video_file(self, target_id: int, fileName: str):
        if self.media_players[target_id]:
            self.media_players[target_id].open_video_file(fileName)

    @log_method_call
    def play(self, target_id=-1):
        if target_id == -1:
            for media_player in self.media_players:
                if media_player:
                    media_player.play()
        elif self.media_players[target_id]:
            self.media_players[target_id].play()

    def set_position(self, position, target_player_id: int = -1):
        if target_player_id == -1:
            for media_player in self.media_players:
                media_player.set_position(position + media_player.video_offset)
        else:
            self.media_players[target_player_id].set_position(
                position + self.media_players[target_player_id].video_offset
            )

    @log_method_call
    def set_view_mode(self, layout_info):
        for i, player_widget in enumerate(self.media_players_widgets):
            player_widget.setHidden(False)

        grid_layout = self.video_players_widget.layout()
        for i, (row, col, rowspan, colspan) in enumerate(layout_info):
            grid_layout.addWidget(
                self.media_players_widgets[i], row, col, rowspan, colspan
            )

    @log_method_call
    def set_view_mode_single(self):
        self.media_players_widgets[0].setHidden(False)
        for player_widget in self.media_players_widgets[1:]:
            player_widget.setHidden(True)

    @log_method_call
    def set_view_mode_even(self):
        self.set_view_mode([(0, 0, 1, 1), (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 1, 1)])

    @log_method_call
    def set_view_mode_portrait(self):
        self.set_view_mode([(0, 0, 3, 1), (0, 1, 1, 1), (1, 1, 1, 1), (2, 1, 1, 1)])

    @log_method_call
    def set_view_mode_landscape(self):
        self.set_view_mode([(0, 0, 1, 3), (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1)])

    def change_offset(self, offset: int, target_id: int = 0):
        self.media_players[target_id].change_offset(offset)

    def set_subtitle_text(self, text):
        self.media_players[0].set_subtitle_text(text)

    def get_offset(self, target_id: int = 0):
        return self.media_players[target_id].get_offset()
