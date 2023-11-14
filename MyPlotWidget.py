from pyqtgraph import PlotWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QDialog
from PopupWindow import TagSelectionDialog
from TagsManager import TagsManager
from config import NAVIGATION_KEY_OFFSET

from util import log_method_call
from LineInfoPair import LineInfoPair


class MyPlotWidget(PlotWidget):
    roi_start = LineInfoPair("ROI Start")
    roi_end = LineInfoPair("ROI End")

    def __init__(
        self,
        get_current_progress_cb,
        create_roi_cb,
        change_video_play_state_cb,
        update_video_progress,
        parent=None,
        background="default",
        plotItem=None,
        **kargs
    ):
        super().__init__(parent, background, plotItem, **kargs)

        self.get_current_progress_cb = get_current_progress_cb
        self.create_roi_cb = create_roi_cb
        self.change_video_play_state_cb = change_video_play_state_cb
        self.update_video_progress = update_video_progress
        self.roi_start.set_plot_widget(self)
        self.roi_end.set_plot_widget(self)

    def keyReleaseEvent(self, key_event):
        if key_event.key() == Qt.Key.Key_S and not key_event.isAutoRepeat():
            self.on_roi_start_pressed()

        if key_event.key() == Qt.Key.Key_E and not key_event.isAutoRepeat():
            self.on_roi_end_pressed()

        if key_event.key() == Qt.Key.Key_M and not key_event.isAutoRepeat():
            self.on_mark_pressed()

        if key_event.key() == Qt.Key.Key_Space and not key_event.isAutoRepeat():
            self.change_video_play_state_cb()

        if key_event.key() == Qt.Key.Key_Left:  # and not key_event.isAutoRepeat():
            self.update_video_progress(
                self.get_current_progress_cb() - NAVIGATION_KEY_OFFSET
            )

        if key_event.key() == Qt.Key.Key_Right:  # and not key_event.isAutoRepeat():
            self.update_video_progress(
                self.get_current_progress_cb() + NAVIGATION_KEY_OFFSET
            )

    @log_method_call
    def on_roi_start_pressed(self):
        current_progress = self.get_current_progress_cb()

        if not self.roi_start.is_marked():
            self.roi_start.mark(current_progress)
        elif self.roi_start.getXPos() == current_progress:
            self.roi_start.clear()
        else:
            self.roi_start.set_pos(current_progress)
        self.validate_roi_position()

    @log_method_call
    def on_roi_end_pressed(self):
        current_progress = self.get_current_progress_cb()

        if not self.roi_end.is_marked():
            self.roi_end.mark(current_progress)
        elif self.roi_end.getXPos() == current_progress:
            self.roi_end.clear()
        else:
            self.roi_end.set_pos(current_progress)
        self.validate_roi_position()

    def validate_roi_position(self):
        if (
            self.roi_start.is_marked()
            and self.roi_end.is_marked()
            and self.roi_end.getXPos() <= self.roi_start.getXPos()
        ):
            QMessageBox.about(
                self, "Warning", "ROI End time cannot be earlier than ROI Start time."
            )
            self.roi_start.clear()
            self.roi_end.clear()

    tags_manager = TagsManager()

    @log_method_call
    def on_mark_pressed(self):
        if not self.roi_start.is_marked() or not self.roi_end.is_marked():
            return

        popup = TagSelectionDialog(self.tags_manager.get_tags())
        x = self.geometry().center().x() - popup.width() / 2
        y = self.geometry().center().y() - popup.height() / 2
        popup.move(int(x), int(y))
        result = popup.exec_()

        if result == QDialog.Accepted:
            selected_item = popup.selected_item
            print("Selected item:", selected_item)
        else:
            return

        self.create_roi_cb(
            self,
            self.roi_start.getXPos(),
            self.roi_end.getXPos(),
            selected_item,
        )

        self.roi_start.clear()
        self.roi_end.clear()
