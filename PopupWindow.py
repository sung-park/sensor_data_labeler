from PyQt5.QtWidgets import *
from collections import defaultdict
from PyQt5.QtCore import Qt, QSize


class myTableWidget(QTableWidget):
    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)

        width += self.verticalHeader().sizeHint().width()

        width += self.verticalScrollBar().sizeHint().width()
        width += self.frameWidth() * 2

        return QSize(width, self.height())


class TagSelectionDialog(QDialog):
    def __init__(self, items):
        super().__init__()

        self.setWindowTitle("Choose one behavior")
        self.layout = QVBoxLayout()

        # Create a dictionary to organize items by type
        items_by_type = defaultdict(list)
        for item in items:
            item_type, item_value = item.split("::", 1)
            items_by_type[item_type].append(item)

        # Determine the number of columns based on the number of types
        num_columns = len(items_by_type)

        self.table_widget = myTableWidget()
        self.table_widget.setColumnCount(num_columns)
        self.table_widget.setHorizontalHeaderLabels(list(items_by_type.keys()))

        max_rows = max(len(items) for items in items_by_type.values())
        self.table_widget.setRowCount(max_rows)

        for col, (item_type, item_values) in enumerate(items_by_type.items()):
            for row, item_value in enumerate(item_values):
                item_widget = QTableWidgetItem(item_value)
                self.table_widget.setItem(row, col, item_widget)

        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.resizeColumnsToContents()

        self.layout.addWidget(self.table_widget)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.item_selected)
        self.layout.addWidget(self.select_button)

        self.setLayout(self.layout)

        self.selected_item = None

        self.adjustSize()

    def item_selected(self):
        selected_items = self.table_widget.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            col = selected_items[0].column()
            self.selected_item = self.table_widget.item(row, col).text()
            self.accept()
        else:
            self.selected_item = None
