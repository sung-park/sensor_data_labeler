from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from TagsManager import TagsManager


class StatsDialog(QDialog):
    table_widget = None

    def __init__(self, total_behavior_durations, main_window: QMainWindow):
        super().__init__()

        self.setWindowTitle("Statistics")

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(3)

        self.table_widget.setHorizontalHeaderLabels(
            ["Type", "Behavior", "Total Duration"]
        )

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        tags = TagsManager().get_tags()

        row = 0
        for tag in tags:
            if tag not in total_behavior_durations:
                total_duration = 0
            else:
                total_duration = total_behavior_durations[tag]

            hours, minutes, seconds, milliseconds = self.milliseconds_to_hms(
                total_duration
            )

            self.table_widget.insertRow(row)
            self.table_widget.setItem(row, 0, QTableWidgetItem(tag.split("::")[0]))

            tag_name_widget = QTableWidgetItem(tag.split("::")[2])
            if total_duration != 0:
                tag_name_widget.setBackground(QColor(245, 245, 220))
            self.table_widget.setItem(row, 1, tag_name_widget)

            duration_item = QTableWidgetItem(
                f"{hours}h {minutes}m {seconds}.{milliseconds}s"
            )
            if total_duration != 0:
                duration_item.setBackground(QColor(245, 245, 220))
            self.table_widget.setItem(row, 2, duration_item)
            row += 1

        self.table_widget.resizeColumnsToContents()
        self.table_widget.resizeRowsToContents()
        self.table_widget.setMinimumWidth(
            int(self.table_widget.horizontalHeader().length() * 1.2)
        )
        self.table_widget.setMinimumHeight(
            int(self.table_widget.verticalHeader().length() * 1.1)
        )

        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)

        self.center(main_window)

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.addAction(copy_action)
        context_menu.exec_(self.table_widget.mapToGlobal(position))

    def copy_to_clipboard(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if selected_rows:
            data = []
            for row in selected_rows:
                row_data = []
                for column in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row.row(), column)
                    row_data.append(item.text())
                data.append(row_data)

            csv_data = "\n".join([",".join(row) for row in data])

            clipboard = QApplication.clipboard()
            clipboard.setText(csv_data)

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

    def milliseconds_to_hms(self, milliseconds):
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return hours, minutes, seconds, milliseconds
