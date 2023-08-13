"""
Main GUI Module
"""

import sys
import logging

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog

from pwctool.pwct_controller import Controller  # pylint: disable=import-error
from pwctool.main_window import Ui_AppDateTool  # pylint: disable=import-error
from pwctool.about_dialog import Ui_appDateToolAbout  # pylint: disable=import-error
from pwctool.error_message_dialog import Ui_ErrorMessageDialog  # pylint: disable=import-error

QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons


class MainView(QMainWindow, Ui_AppDateTool):
    """Main View"""

    def __init__(self):
        super().__init__()
        self.setupUi(self)


class AboutDialog(QDialog, Ui_appDateToolAbout):
    """About Dialog"""

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)


class ErrorMessageDialog(QDialog, Ui_ErrorMessageDialog):
    """Error Message Dialog"""

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)


class App(QApplication):  # pylint: disable=too-few-public-methods
    """Main App Date Tool GUI Application"""

    def __init__(self, sys_argv) -> None:
        super().__init__(sys_argv)

        self.view = MainView()
        self.about = AboutDialog()
        self.error = ErrorMessageDialog()
        self.init_logging()
        self.setStyle("Fusion")
        self.view.show()
        self.controller = Controller(self.view, self.about, self.error)

    def init_logging(self):
        """Create logger that can be accessed from all modules"""

        logger = logging.getLogger("adt_logger")
        logger.setLevel(logging.DEBUG)


def main() -> None:
    """Start the tool by instantiating the GUI and starting it"""
    app = App(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
