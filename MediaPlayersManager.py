from typing import List
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *

from MediaPlayer import MediaPlayer
from util import log_method_call


class MediaPlayersManager:
    def __init__(self, style, main_layout, main_window, update_plot_progress) -> None:
        self.grid_layout = QGridLayout()
        self.media_players: List[MediaPlayer] = []
        for i in range(2):
            for j in range(2):
                media_player = MediaPlayer(
                    style,
                    main_window,
                    update_plot_progress,
                )
                self.media_players.append(media_player)
                self.grid_layout.addWidget(media_player.create_player_widget(), i, j)

        self.video_players_widget = QWidget(main_window)
        self.video_players_widget.setLayout(self.grid_layout)

        main_layout.addWidget(self.video_players_widget)

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
                media_player.set_position(position)
        else:
            self.media_players[target_player_id].set_position(position)
