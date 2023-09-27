import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QFileDialog,
    QLabel,
)
from PyQt5.QtGui import QIcon
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.statusBar()

        openFile = QAction(QIcon("open.png"), "Open", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip("Open New File")
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(openFile)

        self.setWindowTitle("File Dialog")
        self.setGeometry(300, 300, 640, 480)

        self.show()

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, "Open file", "./")

        if fname[0]:
            self.sensor_df = pd.read_csv(fname[0], sep=",", header=0)
            for col in self.sensor_df.columns:
                print(col.strip())

            self.plot_data()

    def plot_data(self):
        self.plot_widget = PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
        self.plot_widget.setLabel("left", "acc (x:red, y:green, z:blue)")
        self.plot_widget.setLabel("bottom", "time")
        x_data = self.sensor_df["timestamp"] / 1000.0
        y_acc_x_data = self.sensor_df[" acc_x"]
        y_acc_y_data = self.sensor_df[" acc_y"]
        y_acc_z_data = self.sensor_df[" acc_z"]

        self.plot_widget.plot(x_data, y_acc_x_data, pen="r")
        self.plot_widget.plot(x_data, y_acc_y_data, pen="g")
        self.plot_widget.plot(x_data, y_acc_z_data, pen="b")

        self.setCentralWidget(self.plot_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
