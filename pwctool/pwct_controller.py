"""
Controller module

Manages GUI-user interactions
"""


import logging
import os
from typing import Any
from functools import partial
import yaml

from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog


from pwctool.config_loader import init_gui_settings_from_config, get_xl_sheet_names
from pwctool.config_generator import generate_configuration_from_gui
from pwctool.pwct_algo_thread import PwcToolAlgoThread
from pwctool.gui_utils import (
    restrict_application_methods,
    enable_disable_waterbodies,
    enable_disable_wettest_month_table,
    update_gui_usecase_change,
    create_blank_config,
    enable_disable_wettest_month_prior,
    enable_disable_koc_vars,
)
from pwctool.validate_inputs import validate_input_files

from pwctool.constants import VERSION

logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py


class Controller:
    """App Date Tool GUI Controller"""

    def __init__(self, main_view, about_dialog, error_dialog) -> None:
        self._view = main_view
        self._about = about_dialog
        self.error_dialog = error_dialog

        self._view.diagnosticWindow.append(f"PWC Prep Tool v{VERSION}")
        self._view.diagnosticWindow.append(
            "For information on use, see the documentation link under 'Help' in the menu bar."
        )
        self._view.diagnosticWindow.append("Please open or enter a configuration.")

        self.saved_config_path = ""

        self._set_default_params()
        self._connect_signals()

    def _set_default_params(self):
        """Parameterizes the GUI with default values"""
        self.new_config("Use Case #1")

    # ======================== MISCELLANEOUS =============================================
    def browse_file_explorer(self, file_type: str):
        """Browse to file location and return path"""
        file_path, _ = QFileDialog.getOpenFileName(self._view, "Open File", "", filter=file_type)
        return file_path

    def browse_to_directory(self):
        """Browse to folder location and return path"""
        directory = QFileDialog.getExistingDirectory(self._view, "Select Folder", "")
        return directory

    def _get_config_settings(self) -> dict[str, Any]:
        """Reads configuration settings from a YAML configuration file and returns them as a dictionary.
        If the user cancels the file explorer, an empty dictionary is returned."""
        file_path = self.browse_file_explorer(file_type="(*.yml)")
        if file_path == "":  # gracefully cancel opening file
            return {}
        with open(file_path, "r") as config_file:  # pylint: disable=unspecified-encoding
            try:
                config_settings = yaml.safe_load(config_file)  # load yml file
            except yaml.YAMLError:
                self.error_dialog.errMsgLabel.setText(
                    "\nERROR:  Something is wrong with the configuration file. Please fix it or create a new one and try again."
                )
                self.error_dialog.exec_()
                return {}
        self.saved_config_path = file_path
        config_file_name = os.path.basename(file_path)
        self._view.diagnosticWindow.append(f"\nLoaded configuration: {config_file_name}")
        return config_settings

    def open_file(self):
        """Loads configuration file settings into the GUI."""
        config_settings = self._get_config_settings()
        if config_settings:
            init_gui_settings_from_config(self._view, config_settings, self.error_dialog)
            restrict_application_methods(self._view)
        else:
            self._view.diagnosticWindow.append("\nNo configuration loaded.")

    def new_config(self, use_case):
        """Creates a blank configuration in the current application. Places defaults."""

        blank_config = create_blank_config(use_case)
        init_gui_settings_from_config(self._view, blank_config, self.error_dialog)
        update_gui_usecase_change(self._view, self.error_dialog)
        if use_case == "Use Case #1":
            enable_disable_waterbodies(self._view)
            enable_disable_wettest_month_table(self._view)
            enable_disable_wettest_month_prior(self._view)

        # reset config path, diagnostic window, and progress bar
        self.saved_config_path = ""

        self._view.diagnosticWindow.clear()
        self._view.diagnosticWindow.append(f"PWC Prep Tool v{VERSION}")
        self._view.diagnosticWindow.append(
            "For information on use, see the documentation link under 'Help' in the menu bar."
        )
        self._view.diagnosticWindow.append("Please open or create a configuration.")
        self._view.progressBar.setValue(0)

    def save_file(self):
        """Saves current configuration to existing file"""

        if self.saved_config_path == "":
            self.save_file_as()
        else:
            current_config = generate_configuration_from_gui(self._view)
            with open(self.saved_config_path, "w") as file:  # pylint: disable=unspecified-encoding
                yaml.dump(current_config, file, sort_keys=False)

    def save_file_as(self):
        """Saves the configuration to a new file"""
        current_config = generate_configuration_from_gui(self._view)

        # save the configuration to a .yml file in the location of the users choice
        file_path, _ = QFileDialog.getSaveFileName(self._view, "Save File", "")
        # Saves the gui parameters to a configuration file
        if file_path != "":
            # Take care of user providing a file extension
            if not file_path.endswith(".yml"):
                file_path = file_path + ".yml"
            with open(file_path, "w") as file:  # pylint: disable=unspecified-encoding
                yaml.dump(current_config, file, sort_keys=False)
        self.saved_config_path = file_path

    def display_about_dialog(self):
        """Displays the about page"""
        dialog = self._about
        dialog.exec_()

    def select_file(self, button, file_type: str):
        """Browses file explore and updates text display with file path"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

    def select_dir(self, button):
        """Browses file explorer for directory"""
        dir_path = self.browse_to_directory()
        button.setText(dir_path)

    def select_apt(self, button, file_type: str):
        """Browses file explorer for APT and updates text display with file path.
        Updates the APT scenario QComboBox with tab names"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

        get_xl_sheet_names(self._view.APTscenario, self._view.agronomicPracticesTableLocation, self.error_dialog, "APT")

    def select_drt(self, button, file_type: str):
        """Browses file explorer for DRT and updates text display with file path.
        Updates the DRT scenario QComboBox with tab names"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

        get_xl_sheet_names(self._view.DRTscenario, self._view.agDriftReductionTableLocation, self.error_dialog, "DRT")

    # ======================== BINS =============================================

    def alter_all_bins_esa(self, state: bool):
        """Alters all the esa bin checkboxes"""
        self._view.bin4CheckBoxESA.setChecked(state)
        self._view.bin7CheckBoxESA.setChecked(state)
        self._view.bin10CheckBoxESA.setChecked(state)

    def alter_all_bins_fifra(self, state: bool):
        """Alters all the fifra bin checkboxes"""
        self._view.bin4CheckBoxFIFRA.setChecked(state)
        self._view.bin7CheckBoxFIFRA.setChecked(state)
        self._view.bin10CheckBoxFIFRA.setChecked(state)

    # ======================== APP METHODs =============================================

    def alter_all_distances_appmeth1(self, state: bool):
        """Alters all distances for app method 1"""

        self._view.appmeth1_000m.setChecked(state)
        self._view.appmeth1_030m.setChecked(state)
        self._view.appmeth1_060m.setChecked(state)
        self._view.appmeth1_090m.setChecked(state)
        self._view.appmeth1_120m.setChecked(state)
        self._view.appmeth1_150m.setChecked(state)

    def alter_all_distances_appmeth2(self, state: bool):
        """Alters all distances for app method 2"""

        self._view.appmeth2_000m.setChecked(state)
        self._view.appmeth2_030m.setChecked(state)
        self._view.appmeth2_060m.setChecked(state)
        self._view.appmeth2_090m.setChecked(state)
        self._view.appmeth2_120m.setChecked(state)
        self._view.appmeth2_150m.setChecked(state)

    def alter_all_depths_appmeth3(self, state: bool):
        """Alters all depths for app method 3"""

        self._view.appmeth3_depth2cm.setChecked(state)
        self._view.appmeth3_depth4cm.setChecked(state)
        self._view.appmeth3_depth6cm.setChecked(state)
        self._view.appmeth3_depth8cm.setChecked(state)
        self._view.appmeth3_depth10cm.setChecked(state)
        self._view.appmeth3_depth12cm.setChecked(state)

    def alter_all_depths_appmeth4(self, state: bool):
        """Alters all depths for app method 4"""

        self._view.appmeth4_depth2cm.setChecked(state)
        self._view.appmeth4_depth4cm.setChecked(state)
        self._view.appmeth4_depth6cm.setChecked(state)
        self._view.appmeth4_depth8cm.setChecked(state)
        self._view.appmeth4_depth10cm.setChecked(state)
        self._view.appmeth4_depth12cm.setChecked(state)

    def alter_all_depths_appmeth5(self, state: bool):
        """Alters all depths for app method 5"""

        self._view.appmeth5_depth4cm.setChecked(state)
        self._view.appmeth5_depth6cm.setChecked(state)
        self._view.appmeth5_depth8cm.setChecked(state)
        self._view.appmeth5_depth10cm.setChecked(state)
        self._view.appmeth5_depth12cm.setChecked(state)

    def alter_all_depths_appmeth6(self, state: bool):
        """Alters all depths for app method 6"""

        self._view.appmeth6_depth2cm.setChecked(state)
        self._view.appmeth6_depth4cm.setChecked(state)
        self._view.appmeth6_depth6cm.setChecked(state)
        self._view.appmeth6_depth8cm.setChecked(state)
        self._view.appmeth6_depth10cm.setChecked(state)
        self._view.appmeth6_depth12cm.setChecked(state)

    def alter_all_depths_appmeth7(self, state: bool):
        """Alters all depths for app method 7"""

        self._view.appmeth7_depth2cm.setChecked(state)
        self._view.appmeth7_depth4cm.setChecked(state)
        self._view.appmeth7_depth6cm.setChecked(state)
        self._view.appmeth7_depth8cm.setChecked(state)
        self._view.appmeth7_depth10cm.setChecked(state)
        self._view.appmeth7_depth12cm.setChecked(state)

    # ======================== EXECUTE TOOL =============================================
    def setup_logging(self, current_config: dict[str, Any]):
        """Sets up log file and diagnostic window"""

        logger.handlers = []  # reset handlers for next run

        log_file_loc = current_config["FILE_PATHS"]["OUTPUT_DIR"]
        log_file_name = current_config["RUN_ID"]
        file_handler = logging.FileHandler(f"{log_file_loc}\\{log_file_name}.log", "w")

        file_handler.setFormatter(logging.Formatter("%(message)s"))
        file_handler.setLevel(logging.DEBUG)  # log file gets everything
        logger.addHandler(file_handler)

    def run_tool(self):
        """Runs the application assignment algorithm"""
        current_config: dict[str, Any] = generate_configuration_from_gui(self._view)
        if validate_input_files(current_config, self.error_dialog):
            self.setup_logging(current_config)
            # start algorithm thread and connect signals to slots
            self.adt_algo_worker = PwcToolAlgoThread(current_config)
            self.adt_algo_worker.start()
            self.adt_algo_worker.update_diagnostics.connect(self.update_diagnostic_window)
            self.adt_algo_worker.update_progress.connect(self.update_progress_bar)

    def update_diagnostic_window(self, val):
        """Append value to diagnostic window (QTextEdit widget)"""
        self._view.diagnosticWindow.append(val)

    def update_progress_bar(self, val):
        """Updates progress bar based on number of runs processed"""
        self._view.progressBar.setValue(int(val))

    # =====================================================================
    def _connect_signals(self):
        """Connects all signals to slots"""

        # fullfull menu actions
        self._view.actionOpen.triggered.connect(self.open_file)
        self._view.actionNewConfig.triggered.connect(lambda: self.new_config("Use Case #1"))
        self._view.actionSave.triggered.connect(self.save_file)
        self._view.actionSave_As.triggered.connect(self.save_file_as)
        self._view.actionDocumentation.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile("./PWC PrepTool Users Guide.pdf"))
        )
        self._view.actionAbout.triggered.connect(self.display_about_dialog)
        self._about.okayAbout.clicked.connect(self._about.reject)
        self.error_dialog.okayError.clicked.connect(self.error_dialog.reject)

        # use case
        self._view.useCaseComboBox.currentTextChanged.connect(
            partial(update_gui_usecase_change, self._view, self.error_dialog)
        )

        # assessment tab
        self._view.fifraRadButton.toggled.connect(partial(enable_disable_waterbodies, self._view))
        self._view.fifraRadButton.toggled.connect(partial(enable_disable_wettest_month_prior, self._view))
        self._view.fifraRadButton.toggled.connect(partial(enable_disable_koc_vars, self._view))
        self._view.esaRadButton.toggled.connect(partial(enable_disable_waterbodies, self._view))
        self._view.esaRadButton.toggled.connect(partial(enable_disable_wettest_month_prior, self._view))
        self._view.esaRadButton.toggled.connect(partial(enable_disable_koc_vars, self._view))

        # date assignment tab
        self._view.wettestMonthPrior.stateChanged.connect(partial(enable_disable_wettest_month_table, self._view))

        # set file locations
        self._view.fileBrowseSourcePWCBatch.clicked.connect(
            partial(self.select_file, self._view.pwcBatchFileLocation, "(*.csv)")
        )
        self._view.fileBrowseOutputLoc.clicked.connect(partial(self.select_dir, self._view.outputFileDirLocation))
        self._view.fileBrowseWettestMonthTable.clicked.connect(
            partial(self.select_file, self._view.wettestMonthTableLocation, "(*.csv)")
        )
        self._view.fileBrowseAPT.clicked.connect(
            partial(self.select_apt, self._view.agronomicPracticesTableLocation, "(*.xlsx)")
        )
        self._view.fileBrowseAPT.clicked.connect(partial(restrict_application_methods, self._view))
        self._view.fileBrowseDRT.clicked.connect(
            partial(self.select_drt, self._view.agDriftReductionTableLocation, "(*.xlsx)")
        )
        self._view.fileBrowseIngrFateParams.clicked.connect(
            partial(self.select_file, self._view.ingrFateParamsLocation, "(*.csv)")
        )

        # update APT and DRT scenario combo box, update app methods based on APT
        self._view.agronomicPracticesTableLocation.editingFinished.connect(
            partial(
                get_xl_sheet_names,
                self._view.APTscenario,
                self._view.agronomicPracticesTableLocation,
                self.error_dialog,
                "APT",
            )
        )
        self._view.agronomicPracticesTableLocation.editingFinished.connect(
            partial(restrict_application_methods, self._view)
        )

        self._view.agDriftReductionTableLocation.editingFinished.connect(
            partial(
                get_xl_sheet_names,
                self._view.DRTscenario,
                self._view.agDriftReductionTableLocation,
                self.error_dialog,
                "DRT",
            )
        )
        self._view.APTscenario.currentTextChanged.connect(partial(restrict_application_methods, self._view))

        # bins
        self._view.binSelectAll.clicked.connect(partial(self.alter_all_bins_esa, True))
        self._view.binClearAll.clicked.connect(partial(self.alter_all_bins_esa, False))
        self._view.fifraWBSelectAll.clicked.connect(partial(self.alter_all_bins_fifra, True))
        self._view.fifraWBClearAll.clicked.connect(partial(self.alter_all_bins_fifra, False))

        # app methods
        self._view.appmeth1_selectalldistances.clicked.connect(partial(self.alter_all_distances_appmeth1, True))
        self._view.appmeth1_clearalldistances.clicked.connect(partial(self.alter_all_distances_appmeth1, False))

        self._view.appmeth2_selectalldistances.clicked.connect(partial(self.alter_all_distances_appmeth2, True))
        self._view.appmeth2_clearalldistances.clicked.connect(partial(self.alter_all_distances_appmeth2, False))

        self._view.appmeth3_selectalldepths.clicked.connect(partial(self.alter_all_depths_appmeth3, True))
        self._view.appmeth3_clearalldepths.clicked.connect(partial(self.alter_all_depths_appmeth3, False))

        self._view.appmeth4_selectalldepths.clicked.connect(partial(self.alter_all_depths_appmeth4, True))
        self._view.appmeth4_clearalldepths.clicked.connect(partial(self.alter_all_depths_appmeth4, False))

        self._view.appmeth5_selectalldepths.clicked.connect(partial(self.alter_all_depths_appmeth5, True))
        self._view.appmeth5_clearalldepths.clicked.connect(partial(self.alter_all_depths_appmeth5, False))

        self._view.appmeth6_selectalldepths.clicked.connect(partial(self.alter_all_depths_appmeth6, True))
        self._view.appmeth6_clearalldepths.clicked.connect(partial(self.alter_all_depths_appmeth6, False))

        self._view.appmeth7_selectalldepths.clicked.connect(partial(self.alter_all_depths_appmeth7, True))
        self._view.appmeth7_clearalldepths.clicked.connect(partial(self.alter_all_depths_appmeth7, False))

        # execute tool
        self._view.runButton.clicked.connect(self.run_tool)
