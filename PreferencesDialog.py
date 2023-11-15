from collections import namedtuple
import json
import os
from PyQt5.QtWidgets import (
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QPushButton,
    QMainWindow,
)

PREFERENCE_FILE_NAME = "settings.json"
Option = namedtuple("Option", ["key", "description", "default"])
OPTION_PLOT_AUTO_SCROLL = Option(
    "plot_auto_scroll",
    "Enable auto-scrolling of sensor data graphs based on video playback",
    True,
)


class PreferencesDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Preferences")

        self.option1 = QCheckBox(OPTION_PLOT_AUTO_SCROLL.description)
        # self.option2 = QCheckBox("옵션 2")
        # self.option3 = QCheckBox("옵션 3")

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.option1)
        # layout.addWidget(self.option2)
        # layout.addWidget(self.option3)
        layout.addWidget(self.ok_button)
        self.setLayout(layout)

        self.load_preferences()

    def get_preferences(self):
        return {
            OPTION_PLOT_AUTO_SCROLL.key: self.option1.isChecked(),
            # "option2": self.option2.isChecked(),
            # "option3": self.option3.isChecked(),
        }

    def get_preference(self, option):
        if option == OPTION_PLOT_AUTO_SCROLL:
            return self.option1.isChecked()
        return False

    def save_preferences(self):
        preferences = self.get_preferences()
        with open(PREFERENCE_FILE_NAME, "w") as json_file:
            json.dump(preferences, json_file)
        self.accept()

    def load_preferences(self):
        if not os.path.exists(PREFERENCE_FILE_NAME):
            self.create_default_preferences()

        with open(PREFERENCE_FILE_NAME, "r") as json_file:
            preferences = json.load(json_file)
            self.option1.setChecked(
                preferences.get(
                    OPTION_PLOT_AUTO_SCROLL.key,
                    OPTION_PLOT_AUTO_SCROLL.default,
                )
            )
            # self.option2.setChecked(preferences.get("option2", False))
            # self.option3.setChecked(preferences.get("option3", False))

    def create_default_preferences(self):
        default_preferences = {
            OPTION_PLOT_AUTO_SCROLL.key: OPTION_PLOT_AUTO_SCROLL.default,
            # "option2": False,
            # "option3": False,
        }
        with open(PREFERENCE_FILE_NAME, "w") as json_file:
            json.dump(default_preferences, json_file)

    def center(self, main_window: QMainWindow):
        screen_geometry = main_window.geometry()
        window_geometry = self.geometry()
        x = (
            screen_geometry.left()
            + (screen_geometry.width() - window_geometry.width()) // 2
        )
        y = (
            screen_geometry.top()
            + (screen_geometry.height() - window_geometry.height()) // 2
        )
        self.move(x, y)
