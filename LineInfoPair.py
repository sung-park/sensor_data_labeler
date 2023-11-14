from pyqtgraph import InfiniteLine, TextItem, PlotWidget
from PyQt5.QtGui import QFont

from config import ROI_MARK_PEN_COLOR


class LineInfoPair:
    infinite_line: InfiniteLine = None
    text_item: TextItem = None
    description = None
    plot_widget = None

    def __init__(self, description: str) -> None:
        self.description = description

    def set_plot_widget(self, plot_widget: PlotWidget) -> None:
        self.plot_widget = plot_widget

    def is_marked(self):
        return self.infinite_line is not None

    def mark(self, position):
        self.infinite_line = InfiniteLine(
            pos=(position, 0),
            angle=90,
            pen=ROI_MARK_PEN_COLOR,
        )

        font = QFont()
        font.setBold(True)
        self.text_item = TextItem(self.description, color=ROI_MARK_PEN_COLOR)
        self.text_item.setFont(font)
        self.text_item.setPos(position, -5)

        self.plot_widget.addItem(self.infinite_line)
        self.plot_widget.addItem(self.text_item)

    def getXPos(self):
        return self.infinite_line.getXPos()

    def clear(self):
        self.plot_widget.removeItem(self.infinite_line)
        self.plot_widget.removeItem(self.text_item)
        self.infinite_line = None
        self.text_item = None

    def set_pos(self, position):
        self.infinite_line.setPos(position)
        self.text_item.setPos(position, -5)
