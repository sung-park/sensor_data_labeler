import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QFileDialog
from PyQt5.QtGui import QIcon
import pandas as pd
from pyqtgraph import PlotWidget
import pyqtgraph as pg


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # self.textEdit = QTextEdit()
        # self.setCentralWidget(self.textEdit)
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

            # f = open(fname[0], "r")

            # with f:
            #     data = f.read()
            #     self.textEdit.setText(data)

    def plot_data(self):
        self.plot_widget = PlotWidget()
        self.plot_widget.setLabel("left", "Y축")
        self.plot_widget.setLabel("bottom", "X축")

        x = self.sensor_df["timestamp"]
        y = self.sensor_df[" acc_x"]

        self.plot_widget.plot(x, y, pen=pg.mkPen("b"))
        self.setCentralWidget(self.plot_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
