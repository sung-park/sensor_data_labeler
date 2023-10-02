import pyqtgraph as pg
from pyqtgraph import PlotWidget, RectROI
import PyQt5
from PyQt5 import QtCore

# from PyQt5.QtCore import Qt


class AnnotationRoi:
    def __init__(
        self,
        plot_widget,
        x_start,
        x_end,
        annotation_text,
    ) -> None:
        self.plot_widget: PlotWidget = plot_widget
        self.x_start = x_start
        self.x_end = x_end
        self.annotation_text = annotation_text

        self.create_roi()
        self.show()

    def create_roi(self):
        # y_min: -22.847815470229374 y_max 24.77754347022937
        y_min, y_max = self.plot_widget.getAxis("left").range

        self.roi: RectROI = RectROI(
            [self.x_start, y_min],
            [
                self.x_end - self.x_start,
                10,
            ],
            pen="y",
            movable=False,
            resizable=False,
            rotatable=False,
        )
        # print("zValue:", self.plot_widget.zValue() + 1)
        self.roi.setZValue(10)

        self.text_item = pg.TextItem(
            text=self.annotation_text, anchor=(0.5, 0.5), color="y"
        )
        roi_rect = self.roi.boundingRect()
        self.text_item.setPos(
            self.x_start + roi_rect.center().x(),
            y_min + roi_rect.center().y(),
        )

    def show(self):
        self.plot_widget.addItem(self.roi)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
        self.roi.sigClicked.connect(roi_mouse_clicked)

        self.plot_widget.addItem(self.text_item)

    def clear(self):
        self.plot_widget.removeItem(self.roi)
        self.plot_widget.removeItem(self.text_item)


def roi_mouse_clicked(roi):
    print("roi_mouse_clicked:", roi)
