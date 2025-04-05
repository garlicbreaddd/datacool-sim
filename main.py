import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtGui import QFont, QIcon

app = QApplication(sys.argv)

class MainWindow(QMainWindow):
    def __init__(self):
        #window setup
        super().__init__()
        self.setWindowTitle("datacenter-sim")

        self.arial = QFont("Arial", 30)

        #component setup
        self.button = QPushButton(self)
        self.button.setGeometry(0,0,20,20)

        self.header = QLabel("Data Center Simulation", self)
        self.header.setFont(self.arial)

        #content setup
        self.content = QVBoxLayout()
        self.content.addWidget(self.header)

        #sidebar setup
        self.sidebar = QVBoxLayout()
        self.sidebar.addWidget(self.button)

        #mainlayout setup
        self.mainlayout = QHBoxLayout()
        self.mainlayout.addLayout(self.content)
        self.mainlayout.addLayout(self.sidebar)

        #finalize
        central_widget = QWidget(self)
        central_widget.setLayout(self.mainlayout)
        self.setCentralWidget(central_widget)
        self.showMaximized()


window = MainWindow()
window.show()

sys.exit(app.exec())