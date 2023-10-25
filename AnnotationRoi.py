from abc import abstractmethod
from typing import List
import pyqtgraph as pg
from pyqtgraph import PlotWidget, RectROI
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QCursor
from TagsManager import TagsManager
from config import TAGS_HEIGHT

from util import log_method_call


class AnnotationRoi:
    def __init__(
        self,
        plot_widget,
        x_start,
        x_end,
        annotation_text,
    ) -> None:
        self._observers: List[AnnotationRoiEventObserver] = []
        self.plot_widget: PlotWidget = plot_widget
        self.x_start = x_start
        self.x_end = x_end
        self.annotation_text = annotation_text
        self.annotation_type = self.annotation_text.split("::")[0]

        self.create_roi()
        self.show()

    tags_manager = TagsManager()

    @log_method_call
    def create_roi(self):
        # y_min: -22.847815470229374 y_max 24.77754347022937
        y_min, y_max = self.plot_widget.getAxis("left").range

        tag_index = self.tags_manager.get_index_of_type(
            self.annotation_text.split("::")[0]
        )

        self.roi: RectROI = RectROI(
            [self.x_start, y_min + (tag_index * TAGS_HEIGHT)],
            [
                self.x_end - self.x_start,
                TAGS_HEIGHT * 0.9,
            ],
            pen="y",
            movable=False,
            resizable=False,
            rotatable=False,
        )
        # print("zValue:", self.plot_widget.zValue() + 1)
        self.roi.setZValue(10)

        self.text_item = pg.TextItem(
            text=self.annotation_text.split("::")[2], anchor=(0.5, 0.5), color="y"
        )
        roi_rect = self.roi.boundingRect()
        self.text_item.setPos(
            self.x_start + roi_rect.center().x(),
            y_min + (tag_index * TAGS_HEIGHT) + roi_rect.center().y(),
        )

    def show(self):
        self.plot_widget.addItem(self.roi)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.MouseButton.RightButton)
        self.roi.sigClicked.connect(self.right_button_clicked)

        self.plot_widget.addItem(self.text_item)

    @log_method_call
    def clear(self):
        self.plot_widget.removeItem(self.roi)
        self.plot_widget.removeItem(self.text_item)

    def right_button_clicked(self, roi):
        self.show_context_menu(roi)

    @log_method_call
    def show_context_menu(self, roi: RectROI):
        menu = QMenu()
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_roi)
        menu.addAction(delete_action)

        cursor = QCursor()
        global_pos = cursor.pos()
        menu.exec_(global_pos)

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def delete_roi(self, roi):
        self.clear()
        for observer in self._observers:
            observer.delete(self)

    def update(self):
        self.clear()
        self.create_roi()
        self.show()

    def __str__(self) -> str:
        return f"Annotation(text={self.annotation_text}, x_start={self.x_start}, x_end={self.x_end})"


class AnnotationRoiEventObserver:
    @abstractmethod
    def delete(self, AnnotationRoi):
        pass
