from PyQt5.QtWidgets import QDialog, QListWidget, QPushButton, QVBoxLayout


class PopupWindow(QDialog):
    def __init__(self, items):
        super().__init__()

        self.setWindowTitle("Choose one behavior")
        self.layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        self.layout.addWidget(self.list_widget)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.item_selected)
        self.layout.addWidget(self.select_button)

        self.setLayout(self.layout)

        self.selected_item = None

    def item_selected(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_item = selected_items[0].text()
            self.accept()
        else:
            self.selected_item = None
