""" Main module"""

import sys
import logging

import yaml
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog

from pwctool.pwct_controller import Controller
from pwctool.main_window import Ui_AppDateTool
from pwctool.about_dialog import Ui_appDateToolAbout

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


class Model:
    """Model class"""

    def __init__(self) -> None:
        pass

    def load_config_file(self, file_path: str):
        """Reads configuration file from file path"""

        with open(file_path, "r") as config_file:
            try:
                config = yaml.safe_load(config_file)  # load yml file
            except yaml.YAMLError as exc:
                print("yaml error")
                print(exc)
        return config

    def save_config_file(self, config, file_path: str):
        """Saves the gui parameters to a configuration file"""
        try:
            with open(file_path, "w") as file:
                yaml.dump(config, file, sort_keys=False)
        except FileNotFoundError:
            pass


class App(QApplication):  # pylint: disable=too-few-public-methods
    """Main App Date Tool GUI Application"""

    def __init__(self, sys_argv) -> None:
        super().__init__(sys_argv)

        self.model = Model()
        self.view = MainView()  # create instance of main view
        self.about = AboutDialog()
        self.init_logging()
        self.setStyle("Fusion")
        self.view.show()
        self.controller = Controller(self.model, self.view, self.about)

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
