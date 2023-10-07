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
                    update_plot_progress,
                )
                self.media_players.append(media_player)
                widget = media_player.create_player_widget()
                self.media_players_widgets.append(widget)
                grid_layout.addWidget(widget, i, j)

        self.video_players_widget: QWidget = QWidget(main_window)
        self.video_players_widget.setLayout(grid_layout)

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

    def clear_grid_layout(layout) -> List[QWidget]:
        widgets = []
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widgets.append(child.wiget())
                child.widget().deleteLater()
        return widgets

    @log_method_call
    def set_view_mode_even(self):
        grid_layout: QGridLayout = self.video_players_widget.layout()
        grid_layout.addWidget(self.media_players_widgets[0], 0, 0)
        grid_layout.addWidget(self.media_players_widgets[1], 0, 1)
        grid_layout.addWidget(self.media_players_widgets[2], 1, 0)
        grid_layout.addWidget(self.media_players_widgets[3], 1, 1)

    @log_method_call
    def set_view_mode_portrait(self):
        grid_layout: QGridLayout = self.video_players_widget.layout()
        grid_layout.addWidget(self.media_players_widgets[0], 0, 0, 3, 1)
        grid_layout.addWidget(self.media_players_widgets[1], 0, 1)
        grid_layout.addWidget(self.media_players_widgets[2], 1, 1)
        grid_layout.addWidget(self.media_players_widgets[3], 2, 1)

    @log_method_call
    def set_view_mode_landscape(self):
        grid_layout: QGridLayout = self.video_players_widget.layout()
        grid_layout.addWidget(self.media_players_widgets[0], 0, 0, 1, 3)
        grid_layout.addWidget(self.media_players_widgets[1], 1, 0)
        grid_layout.addWidget(self.media_players_widgets[2], 1, 1)
        grid_layout.addWidget(self.media_players_widgets[3], 1, 2)
