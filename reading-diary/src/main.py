import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from main_window import MainWindow
from database import Database


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Читательский дневник")

    db = Database()
    db.init_db()

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()