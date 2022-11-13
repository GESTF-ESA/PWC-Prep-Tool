"""MAIN WINDOW CONTROLLER"""

import os
import logging
from typing import Any, Dict
from functools import partial

from PyQt5.QtWidgets import QFileDialog, QCheckBox
import pandas as pd

from pwctool.pwct_algo_thread import AdtAlgoThread

__model_version__ = "0.0.1"
logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py


class Controller:
    """App Date Tool GUI Controller"""

    DEFAULT_DIR = "D:"  # default directory for file explorer browsing
    ALL_HUCS = "1,2,3,4,5,6,7,8,9,10a,10b,11a,11b,12a,12b,13,14,15a,15b,16a,16b,17a,17b,18a,18b,19a,19b,20a,20b,21"
    ALL_BINS = "1,4,7"
    ALL_DISTANCES = "000m,030m,060m,090m,120m,150m"

    def __init__(self, model, main_view, about_dialog) -> None:
        self._model = model
        self._view = main_view
        self._about = about_dialog

        self._view.diagnosticWindow.append("Welcome to the App Dates Tool.")
        self._view.diagnosticWindow.append("Please open or enter a configuration.")
        self._view.diagnosticWindow.append("See the documentation under 'Help' in the toolbar.")

        self.saved_config_path = ""

        self._use_case_descriptions = {
            "Use Case #1": "I want to generate a PWC batch input file from scratch",
            "Use Case #2": "I want to QC an existing batch file",
            "Use Case #3": "I want to QC an existing batch file and refine application information",
        }

        self.set_default_params()
        self._connect_signals()

    def set_default_params(self):
        """Parameterizes the GUI with default values"""
        self._view.checkBoxRD_000m.setChecked(True)
        self._view.resADJFactor.setText("0.587")
        self._view.progressBar.setValue(0)
        self._view.APTscenario.addItem("Please specify APT file")
        self._view.DRTscenario.addItem("Please specify DRT file")
        self._view.useCaseComboBox.setCurrentText("Use Case #1")
        self.update_use_case_description()
        self.deactivate_irrelavent_widgets()

    # ======================== MISCELLANEOUS =============================================

    def update_text_display(self, text_display, check_box, check_box_id: str):
        """Updates text edit widget based on a check box state and identifier"""

        current_selection = text_display.text()  # get current text from text edit widget

        # if there is a selection already, store it
        new_selection = current_selection.split(",") if current_selection else []

        state = check_box.checkState()  # get check box state
        if state == 0:  # not checked
            try:
                new_selection.remove(check_box_id)  # remove selection from text edit display
            except ValueError:
                new_selection = []
            text_display.setText(",".join(sorted(new_selection)))

        else:  # checked (state==2)
            if check_box_id not in new_selection:
                new_selection.append(check_box_id)  # add selection to text edit
            text_display.setText(",".join(sorted(new_selection)))

    def browse_file_explorer(self, file_type: str):
        """Browse to file location and return path"""
        file_path, _ = QFileDialog.getOpenFileName(self._view, "Open File", Controller.DEFAULT_DIR, filter=file_type)
        return file_path

    def browse_to_directory(self):
        """Browse to folder location and return path"""
        directory = QFileDialog.getExistingDirectory(self._view, "Select Folder", Controller.DEFAULT_DIR)
        return directory

    # ======================== FULLFILL MENU ACTIONS =============================================
    def set_exposure_states(self, exposure_configuration: Dict[str, list]):
        """Sets the exposure parameters when loading a configuration file"""

        def set_exp_checkbox(exposure_config: Dict[str, list], rd_checkbox, d_checkbox, distance: str):
            """Sets exposure check box for runoff/drift and drift only options when loading a configuration file."""
            distance_config = exposure_config[distance]

            if "RD" in distance_config:
                rd_checkbox.setChecked(True)
            else:
                rd_checkbox.setChecked(False)

            if "D" in distance_config:
                d_checkbox.setChecked(True)
            else:
                d_checkbox.setChecked(False)

        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_000m, self._view.checkBoxD_000m, "000m")
        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_030m, self._view.checkBoxD_030m, "030m")
        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_060m, self._view.checkBoxD_060m, "060m")
        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_090m, self._view.checkBoxD_090m, "090m")
        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_120m, self._view.checkBoxD_120m, "120m")
        set_exp_checkbox(exposure_configuration, self._view.checkBoxRD_150m, self._view.checkBoxD_150m, "150m")

    def populate_gui_from_config(self, config: Dict[str, Any]):
        """Populates gui with information in saved config file"""

        # use case
        self._view.useCaseComboBox.setCurrentText(config["USE_CASE"])

        # file paths
        self._view.pwcBatchFileLocation.setText(config["FILE_PATHS"]["PWC_BATCH_CSV"])
        self._view.outputFileDirLocation.setText(config["FILE_PATHS"]["OUTPUT_DIR"])
        self._view.wettestMonthTableLocation.setText(config["FILE_PATHS"]["WETTEST_MONTH_CSV"])
        self._view.agronomicPracticesTableLocation.setText(config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"])
        self._view.scenarioFilesDirectoryLocation.setText(config["FILE_PATHS"]["SCENARIO_FILES_PATH"])
        self._view.agDriftReductionTableLocation.setText(config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"])
        self._view.ingrFateParamsLocation.setText(config["FILE_PATHS"]["INGR_FATE_PARAMS"])
        self._view.stateToHucLookupTableLocation.setText(config["FILE_PATHS"]["STATE_TO_HUC"])
        self._view.binToLandscapeParamsLocation.setText(config["FILE_PATHS"]["BIN_TO_LANDSCAPE"])

        # bins
        self._view.binsDisplaySelect.setText(",".join([str(i) for i in config["BINS"]]))

        # app distances
        self._view.groundDisplaySelect.setText(",".join([str(i) for i in config["APP_DISTANCES"]["Ground"]]))
        self._view.granDisplaySelect.setText(",".join([str(i) for i in config["APP_DISTANCES"]["Granular"]]))
        self._view.aerialDisplaySelect.setText(",".join([str(i) for i in config["APP_DISTANCES"]["Aerial"]]))

        # exposure states
        self.set_exposure_states(config["EXPOSURE_TYPES"])

        # other
        self._view.APTscenario.clear()
        if config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"] == "":  # APT file location is not specified
            self._view.APTscenario.addItem("Please specify APT file")
        else:
            apt_sheets: list = pd.ExcelFile(config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"]).sheet_names
            self._view.APTscenario.addItems(apt_sheets)
            if config["APT_SCENARIO"] != "Please specify APT file":
                self._view.APTscenario.setCurrentText(config["APT_SCENARIO"])

        self._view.DRTscenario.clear()
        if config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"] == "":  # DRT file location is not specified
            self._view.DRTscenario.addItem("Please specify DRT file")
        else:
            drt_sheets: list = pd.ExcelFile(config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"]).sheet_names
            self._view.DRTscenario.addItems(drt_sheets)
            if config["DRT_SCENARIO"] != "Please specify DRT file":
                self._view.DRTscenario.setCurrentText(config["DRT_SCENARIO"])

        self._view.resADJFactor.setText(str(config["RESIDENTIAL_ADJ_FACTOR"]))
        self._view.runId.setText(config["RUN_ID"])

        # date assignment
        self._view.datePriorComboBox.clear()
        self._view.datePriorComboBox.addItems(["Max App. Rate", "Wettest Month"])
        if config["DATE_PRIORITIZATION"] == "Max App. Rate":
            self._view.datePriorComboBox.setCurrentIndex(0)
        elif config["DATE_PRIORITIZATION"] == "Wettest Month":
            self._view.datePriorComboBox.setCurrentIndex(1)
        else:
            self._view.datePriorComboBox.setCurrentIndex(0)

        self._view.datePriorComboBox.setCurrentText(config["DATE_PRIORITIZATION"])
        self._view.randomStartDatesBool.setChecked(config["RANDOM_START_DATES"])
        self._view.randomSeed.setText(str(config["RANDOM_SEED"]))

    def get_exposure_selection(self, config_exp: Dict):
        """Updates config file with exposure options when saving a configuration"""

        def check_state_exposure(config_exp: Dict, rd_checkbox, d_checkbox, distance: str) -> Dict:
            """Assigns exposure types to proximity zones based on check boxes"""

            state_rd = rd_checkbox.checkState()
            state_d = d_checkbox.checkState()

            if state_rd == 2 and state_d == 2:
                config_exp[distance] = ["RD", "D"]
            elif state_rd == 2 and state_d == 0:
                config_exp[distance] = ["RD"]
            elif state_rd == 0 and state_d == 2:
                config_exp[distance] = ["D"]
            elif state_rd == 0 and state_d == 0:
                config_exp[distance] = [""]

            return config_exp

        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_000m, self._view.checkBoxD_000m, "000m")
        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_030m, self._view.checkBoxD_030m, "030m")
        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_060m, self._view.checkBoxD_060m, "060m")
        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_090m, self._view.checkBoxD_090m, "090m")
        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_120m, self._view.checkBoxD_120m, "120m")
        config_exp = check_state_exposure(config_exp, self._view.checkBoxRD_150m, self._view.checkBoxD_150m, "150m")

        return config_exp

    def generate_configuration_from_gui(self) -> Dict[str, Any]:
        """Generates a configuration from the gui"""

        config: Dict[str, Any] = {}

        config["RUN_ID"] = self._view.runId.text()
        config["USE_CASE"] = self._view.useCaseComboBox.currentText()
        config["FILE_PATHS"] = {}
        config["APP_DISTANCES"] = {}
        config["EXPOSURE_TYPES"] = {}

        # update the template configuration file with entered info
        config["FILE_PATHS"]["PWC_BATCH_CSV"] = self._view.pwcBatchFileLocation.text()
        config["FILE_PATHS"]["OUTPUT_DIR"] = self._view.outputFileDirLocation.text()
        config["FILE_PATHS"]["WETTEST_MONTH_CSV"] = self._view.wettestMonthTableLocation.text()
        config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"] = self._view.agronomicPracticesTableLocation.text()
        config["FILE_PATHS"]["SCENARIO_FILES_PATH"] = self._view.scenarioFilesDirectoryLocation.text()
        config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"] = self._view.agDriftReductionTableLocation.text()
        config["FILE_PATHS"]["INGR_FATE_PARAMS"] = self._view.ingrFateParamsLocation.text()
        config["FILE_PATHS"]["STATE_TO_HUC"] = self._view.stateToHucLookupTableLocation.text()
        config["FILE_PATHS"]["BIN_TO_LANDSCAPE"] = self._view.binToLandscapeParamsLocation.text()

        config["BINS"] = [
            str(i)
            for i in self._view.binsDisplaySelect.text().split(",")
            if not self._view.binsDisplaySelect.text() == ""
        ]

        config["APP_DISTANCES"]["Ground"] = [
            i
            for i in self._view.groundDisplaySelect.text().split(",")
            if not self._view.groundDisplaySelect.text() == ""
        ]
        config["APP_DISTANCES"]["Granular"] = [
            i for i in self._view.granDisplaySelect.text().split(",") if not self._view.granDisplaySelect.text() == ""
        ]
        config["APP_DISTANCES"]["Aerial"] = [
            i
            for i in self._view.aerialDisplaySelect.text().split(",")
            if not self._view.aerialDisplaySelect.text() == ""
        ]

        config["EXPOSURE_TYPES"] = self.get_exposure_selection(config["EXPOSURE_TYPES"])
        config["APT_SCENARIO"] = self._view.APTscenario.currentText()
        config["DRT_SCENARIO"] = self._view.DRTscenario.currentText()

        try:
            config["RESIDENTIAL_ADJ_FACTOR"] = float(self._view.resADJFactor.text())
        except ValueError:
            config["RESIDENTIAL_ADJ_FACTOR"] = 0.0

        def get_checkbox_state_bool(check_box) -> bool:
            """Determine the random start date selection"""
            state = check_box.checkState()
            if state == 0:
                return False
            return True

        config["RANDOM_START_DATES"] = get_checkbox_state_bool(self._view.randomStartDatesBool)
        config["RANDOM_SEED"] = self._view.randomSeed.text()

        config["DATE_PRIORITIZATION"] = self._view.datePriorComboBox.currentText()

        return config

    def open_file(self):
        """Allows user to open saved configuration file"""
        file_path = self.browse_file_explorer(file_type="(*.yml)")
        if file_path == "":  # needed to gracefully cancel opening file
            pass
        else:
            opened_config = self._model.load_config_file(file_path)
            self.populate_gui_from_config(opened_config)
            self.saved_config_path = file_path

            config_file_name = os.path.basename(file_path)
            self._view.diagnosticWindow.append(f"\nLoaded configuration: {config_file_name}")

            self._view.progressBar.setValue(0)

            # TODO: check file paths exist function

    def new_config(self):
        """Creates a blank configuration in the current application"""

        config = {}
        config["USE_CASE"] = "Use Case #1"
        config["FILE_PATHS"] = {}
        config["APP_DISTANCES"] = {}
        config["EXPOSURE_TYPES"] = {}
        config["FILE_PATHS"]["PWC_BATCH_CSV"] = ""
        config["FILE_PATHS"]["OUTPUT_DIR"] = ""
        config["FILE_PATHS"]["WETTEST_MONTH_CSV"] = ""
        config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"] = ""
        config["FILE_PATHS"]["SCENARIO_FILES_PATH"] = ""
        config["FILE_PATHS"]["INGR_FATE_PARAMS"] = ""
        config["FILE_PATHS"]["STATE_TO_HUC"] = ""
        config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"] = ""
        config["FILE_PATHS"]["BIN_TO_LANDSCAPE"] = ""
        config["BINS"] = []
        config["APP_DISTANCES"]["Ground"] = ["000m"]
        config["APP_DISTANCES"]["Granular"] = []
        config["APP_DISTANCES"]["Aerial"] = ["000m"]
        config["EXPOSURE_TYPES"] = {
            "000m": ["RD", "D"],
            "030m": [],
            "060m": [],
            "090m": [],
            "120m": [],
            "150m": [],
            "300m": [],
        }
        config["APT_SCENARIO"] = "Please specify APT file"
        config["DRT_SCENARIO"] = "Please specify DRT file"
        config["RESIDENTIAL_ADJ_FACTOR"] = 0.587
        config["RANDOM_START_DATES"] = False
        config["RANDOM_SEED"] = ""
        config["RUN_ID"] = ""
        config["DATE_PRIORITIZATION"] = ""

        self.populate_gui_from_config(config)
        self.saved_config_path = ""

        self._view.diagnosticWindow.clear()
        self._view.diagnosticWindow.append("Welcome to the App Dates Tool.")
        self._view.diagnosticWindow.append("Please open or enter a configuration.")
        self._view.diagnosticWindow.append("See the documentation under 'Help' in the toolbar.")

        self._view.progressBar.setValue(0)

    def save_file(self):
        """Saves current configuration to existing file"""

        if self.saved_config_path == "":
            self.save_file_as()
        else:
            current_config = self.generate_configuration_from_gui()
            self._model.save_config_file(current_config, self.saved_config_path)

    def save_file_as(self):
        """Saves the configuration to a new file"""
        current_config = self.generate_configuration_from_gui()

        # save the configuration to a .yml file in the location of the users choice
        file_path, _ = QFileDialog.getSaveFileName(self._view, "Save File", Controller.DEFAULT_DIR)
        file_path = f"{file_path}.yml"
        self._model.save_config_file(current_config, file_path)
        self.saved_config_path = file_path

    def display_about_dialog(self):
        """Displays the about page"""
        dialog = self._about
        dialog.exec()

    # ======================== USE CASE SELECTION =============================================

    def update_use_case_description(self):
        """Updates the use case description when a new use case is selected"""
        new_use_case = self._view.useCaseComboBox.currentText()
        self._view.useCaseLabel.setText(self._use_case_descriptions[new_use_case])

        self.clear_widget_deactivation()

        # clear update widgets
        config = {}
        config["USE_CASE"] = new_use_case
        config["FILE_PATHS"] = {}
        config["APP_DISTANCES"] = {}
        config["EXPOSURE_TYPES"] = {}
        config["FILE_PATHS"]["PWC_BATCH_CSV"] = ""
        config["FILE_PATHS"]["OUTPUT_DIR"] = ""
        config["FILE_PATHS"]["WETTEST_MONTH_CSV"] = ""
        config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"] = ""
        config["FILE_PATHS"]["SCENARIO_FILES_PATH"] = ""
        config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"] = ""
        config["FILE_PATHS"]["INGR_FATE_PARAMS"] = ""
        config["FILE_PATHS"]["STATE_TO_HUC"] = ""
        config["FILE_PATHS"]["BIN_TO_LANDSCAPE"] = ""
        config["BINS"] = []
        config["APP_DISTANCES"]["Ground"] = ["000m"]
        config["APP_DISTANCES"]["Granular"] = []
        config["APP_DISTANCES"]["Aerial"] = ["000m"]
        config["EXPOSURE_TYPES"] = {
            "000m": ["RD", "D"],
            "030m": [],
            "060m": [],
            "090m": [],
            "120m": [],
            "150m": [],
            "300m": [],
        }
        config["APT_SCENARIO"] = "Please specify APT file"
        config["DRT_SCENARIO"] = "Please specify DRT file"
        config["RESIDENTIAL_ADJ_FACTOR"] = 0.587
        config["RANDOM_START_DATES"] = False
        config["RANDOM_SEED"] = ""
        config["RUN_ID"] = ""
        config["DATE_PRIORITIZATION"] = ""

        self.populate_gui_from_config(config)
        self.saved_config_path = ""

    def deactivate_irrelavent_widgets(self):
        """Deactivates widgets that are not relavent for the use case."""

        new_use_case = self._view.useCaseComboBox.currentText()

        if new_use_case == "Use Case #1":
            # disable source batch file parameter
            self._view.pwcBatchFileLocation.setEnabled(False)
            self._view.pwcBatchFileLabel.setStyleSheet("color: grey")
            self._view.fileBrowseSourcePWCBatch.setEnabled(False)

        else:  # use case 2 and 3
            # disable wettest month widgets
            self._view.wettestMonthTableLocation.setEnabled(False)
            self._view.fileBrowseWettestMonthTable.setStyleSheet("color: grey")
            self._view.fileBrowseWettestMonthTable.setEnabled(False)
            self._view.wettestMonthTableLabel.setStyleSheet("color: grey")
            # other tables
            self._view.ingrFateParamsLocation.setEnabled(False)
            self._view.fileBrowseIngrFateParams.setStyleSheet("color: grey")
            self._view.fileBrowseIngrFateParams.setEnabled(False)
            self._view.ingrFateParamsLabel.setStyleSheet("color: grey")
            self._view.stateToHucLookupTableLocation.setEnabled(False)
            self._view.stateToHUCLabel.setStyleSheet("color: grey")
            self._view.fileBrowseStateToHuc.setStyleSheet("color: grey")
            self._view.fileBrowseStateToHuc.setEnabled(False)
            self._view.binToLandscapeParamsLocation.setEnabled(False)
            self._view.fileBrowseBintoLandscapeParams.setStyleSheet("color: grey")
            self._view.fileBrowseBintoLandscapeParams.setEnabled(False)
            self._view.binToLandscapeTable.setStyleSheet("color: grey")

            # disable bin tab
            self._view.binsParamDescription.setStyleSheet("color: grey")
            self._view.binsDisplaySelect.setEnabled(False)
            self._view.binClearDisplay.setEnabled(False)
            self._view.binSelectAll.setEnabled(False)
            self._view.bin1CheckBox.setEnabled(False)
            self._view.bin4CheckBox.setEnabled(False)
            self._view.bin7CheckBox.setEnabled(False)
            # disable app distances tab
            self._view.appDistancesDescription.setStyleSheet("color: grey")
            self._view.groundDisplaySelect.setEnabled(False)
            self._view.groundClearDisplay.setEnabled(False)
            self._view.groundSelectAll.setEnabled(False)
            self._view.ground000m.setEnabled(False)
            self._view.ground030m.setEnabled(False)
            self._view.ground060m.setEnabled(False)
            self._view.ground090m.setEnabled(False)
            self._view.ground120m.setEnabled(False)
            self._view.ground150m.setEnabled(False)
            self._view.granDisplaySelect.setEnabled(False)
            self._view.granularClearDisplay.setEnabled(False)
            self._view.granularSelectAll.setEnabled(False)
            self._view.gran000m.setEnabled(False)
            self._view.gran030m.setEnabled(False)
            self._view.gran060m.setEnabled(False)
            self._view.gran090m.setEnabled(False)
            self._view.gran120m.setEnabled(False)
            self._view.gran150m.setEnabled(False)
            self._view.aerialDisplaySelect.setEnabled(False)
            self._view.aerialClearDisplay.setEnabled(False)
            self._view.aerialSelectAll.setEnabled(False)
            self._view.aerial000m.setEnabled(False)
            self._view.aerial030m.setEnabled(False)
            self._view.aerial060m.setEnabled(False)
            self._view.aerial090m.setEnabled(False)
            self._view.aerial120m.setEnabled(False)
            self._view.aerial150m.setEnabled(False)
            # exposure types descriptions
            self._view.exposureTypesDescription.setStyleSheet("color: grey")
            self._view.exposureTypesDescription_4.setStyleSheet("color: grey")
            self._view.exposureTypesDescription_5.setStyleSheet("color: grey")
            self._view.checkBoxRD_000m.setEnabled(False)
            self._view.checkBoxRD_030m.setEnabled(False)
            self._view.checkBoxRD_060m.setEnabled(False)
            self._view.checkBoxRD_090m.setEnabled(False)
            self._view.checkBoxRD_120m.setEnabled(False)
            self._view.checkBoxRD_150m.setEnabled(False)
            self._view.checkBoxD_000m.setEnabled(False)
            self._view.checkBoxD_030m.setEnabled(False)
            self._view.checkBoxD_060m.setEnabled(False)
            self._view.checkBoxD_090m.setEnabled(False)
            self._view.checkBoxD_120m.setEnabled(False)
            self._view.checkBoxD_150m.setEnabled(False)
            # date assignment parameters
            self._view.datePriorComboBox.setEnabled(False)
            self._view.randomStartDatesBool.setEnabled(False)
            self._view.randomSeed.setEnabled(False)
            self._view.label_15.setStyleSheet("color: grey")
            self._view.label_13.setStyleSheet("color: grey")
            self._view.label_14.setStyleSheet("color: grey")
            # residential ADJ factor
            self._view.label_2.setStyleSheet("color: grey")
            self._view.resADJFactor.setEnabled(False)

    def clear_widget_deactivation(self):
        """Enables all wiidgets and resets styles"""
        # enable source batch file parameter
        self._view.pwcBatchFileLocation.setEnabled(True)
        self._view.pwcBatchFileLabel.setStyleSheet("color: black")
        self._view.fileBrowseSourcePWCBatch.setEnabled(True)

        # other tables
        self._view.wettestMonthTableLocation.setEnabled(True)
        self._view.fileBrowseWettestMonthTable.setStyleSheet("color: black")
        self._view.fileBrowseWettestMonthTable.setEnabled(True)
        self._view.wettestMonthTableLabel.setStyleSheet("color: black")
        self._view.ingrFateParamsLocation.setEnabled(True)
        self._view.fileBrowseIngrFateParams.setStyleSheet("color: black")
        self._view.fileBrowseIngrFateParams.setEnabled(True)
        self._view.ingrFateParamsLabel.setStyleSheet("color: black")
        self._view.stateToHucLookupTableLocation.setEnabled(True)
        self._view.stateToHUCLabel.setStyleSheet("color: black")
        self._view.fileBrowseStateToHuc.setStyleSheet("color: black")
        self._view.fileBrowseStateToHuc.setEnabled(True)
        self._view.binToLandscapeParamsLocation.setEnabled(True)
        self._view.fileBrowseBintoLandscapeParams.setStyleSheet("color: black")
        self._view.fileBrowseBintoLandscapeParams.setEnabled(True)
        self._view.binToLandscapeTable.setStyleSheet("color: black")

        # disable bin tab
        self._view.binsParamDescription.setStyleSheet("color: black")
        self._view.binsDisplaySelect.setEnabled(True)
        self._view.binClearDisplay.setEnabled(True)
        self._view.binSelectAll.setEnabled(True)
        self._view.bin1CheckBox.setEnabled(True)
        self._view.bin4CheckBox.setEnabled(True)
        self._view.bin7CheckBox.setEnabled(True)
        # disable app distances tab
        self._view.appDistancesDescription.setStyleSheet("color: black")
        self._view.groundDisplaySelect.setEnabled(True)
        self._view.groundClearDisplay.setEnabled(True)
        self._view.groundSelectAll.setEnabled(True)
        self._view.ground000m.setEnabled(True)
        self._view.ground030m.setEnabled(True)
        self._view.ground060m.setEnabled(True)
        self._view.ground090m.setEnabled(True)
        self._view.ground120m.setEnabled(True)
        self._view.ground150m.setEnabled(True)
        self._view.granDisplaySelect.setEnabled(True)
        self._view.granularClearDisplay.setEnabled(True)
        self._view.granularSelectAll.setEnabled(True)
        self._view.gran000m.setEnabled(True)
        self._view.gran030m.setEnabled(True)
        self._view.gran060m.setEnabled(True)
        self._view.gran090m.setEnabled(True)
        self._view.gran120m.setEnabled(True)
        self._view.gran150m.setEnabled(True)
        self._view.aerialDisplaySelect.setEnabled(True)
        self._view.aerialClearDisplay.setEnabled(True)
        self._view.aerialSelectAll.setEnabled(True)
        self._view.aerial000m.setEnabled(True)
        self._view.aerial030m.setEnabled(True)
        self._view.aerial060m.setEnabled(True)
        self._view.aerial090m.setEnabled(True)
        self._view.aerial120m.setEnabled(True)
        self._view.aerial150m.setEnabled(True)
        # exposure types descriptions
        self._view.exposureTypesDescription.setStyleSheet("color: black")
        self._view.exposureTypesDescription_4.setStyleSheet("color: black")
        self._view.exposureTypesDescription_5.setStyleSheet("color: black")
        self._view.checkBoxRD_000m.setEnabled(True)
        self._view.checkBoxRD_030m.setEnabled(True)
        self._view.checkBoxRD_060m.setEnabled(True)
        self._view.checkBoxRD_090m.setEnabled(True)
        self._view.checkBoxRD_120m.setEnabled(True)
        self._view.checkBoxRD_150m.setEnabled(True)
        self._view.checkBoxD_000m.setEnabled(True)
        self._view.checkBoxD_030m.setEnabled(True)
        self._view.checkBoxD_060m.setEnabled(True)
        self._view.checkBoxD_090m.setEnabled(True)
        self._view.checkBoxD_120m.setEnabled(True)
        self._view.checkBoxD_150m.setEnabled(True)
        # date assignment parameters
        self._view.datePriorComboBox.setEnabled(True)
        self._view.randomStartDatesBool.setEnabled(True)
        self._view.randomSeed.setEnabled(True)
        self._view.label_15.setStyleSheet("color: black")
        self._view.label_13.setStyleSheet("color: black")
        self._view.label_14.setStyleSheet("color: black")
        # residential ADJ factor
        self._view.label_2.setStyleSheet("color: black")
        self._view.resADJFactor.setEnabled(True)

    # ======================== FILE LOCATIONS =============================================

    def select_file(self, button, file_type: str):
        """Browses file explore and updates text display with file path"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

    def select_dir(self, button):
        """Browses file explorer for directory"""
        dir_path = self.browse_to_directory()
        button.setText(dir_path)

    def get_xl_sheet_names(self, drop_down, location):
        """Gets the xl sheet names for the APT or DRT and updates drop down"""

        file_path = location.text()
        drop_down.clear()
        try:
            sheets: list = pd.ExcelFile(file_path).sheet_names
            drop_down.clear()
            drop_down.addItems(sheets)
        except AssertionError:  # file path is "" upon cancel file brows
            pass
        except OSError:
            pass

    def select_apt(self, button, file_type: str):
        """Browses file explorer for APT and updates text display with file path.
        Updates the APT scenario QComboBox with tab names"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

        self.get_xl_sheet_names(self._view.APTscenario, self._view.agronomicPracticesTableLocation)

    def select_drt(self, button, file_type: str):
        """Browses file explorer for DRT and updates text display with file path.
        Updates the DRT scenario QComboBox with tab names"""
        file_path = self.browse_file_explorer(file_type)
        button.setText(file_path)

        self.get_xl_sheet_names(self._view.DRTscenario, self._view.agDriftReductionTableLocation)

    # ======================== BINS =============================================

    def update_bin_display(self, check_box, bin_id: str):
        """Updates the bin selection based on bin checkboxes"""
        self.update_text_display(self._view.binsDisplaySelect, check_box, bin_id)

    def clear_bin_display(self):
        """Clears the bin selection display and unchecks the check boxes"""
        self._view.binsDisplaySelect.setText("")  # remove all hucs from selection
        for bin_check_box in self._view.binsParamFrame.findChildren(QCheckBox):
            bin_check_box.setChecked(False)

    # ======================== APP DISTANCES =============================================

    def update_app_display(self, check_box, distance: str, kind: str):
        """Updates the app distance text edits based on the check box and kind of application"""
        if kind == "gd":  # ground
            self.update_text_display(self._view.groundDisplaySelect, check_box, distance)
        elif kind == "gn":  # gran
            self.update_text_display(self._view.granDisplaySelect, check_box, distance)
        else:  # aerial
            self.update_text_display(self._view.aerialDisplaySelect, check_box, distance)

    def clear_appdist_ground_selection(self):
        """Clears the app distance ground selection display and unchecks the check boxes"""
        self._view.groundDisplaySelect.setText("")  # remove all hucs from selection
        for ground_check_box in self._view.groundAppDistanceFrame.findChildren(QCheckBox):
            ground_check_box.setChecked(False)

    def clear_appdist_gran_selection(self):
        """Clears the app distance granular selection display and unchecks the check boxes"""
        self._view.granDisplaySelect.setText("")  # remove all hucs from selection
        for gran_check_box in self._view.granAppDistanceFrame.findChildren(QCheckBox):
            gran_check_box.setChecked(False)

    def clear_appdist_aerial_selection(self):
        """Clears the app distance aerial selection display and unchecks the check boxes"""
        self._view.aerialDisplaySelect.setText("")  # remove all hucs from selection
        for aerial_check_box in self._view.aerialAppDistanceFrame.findChildren(QCheckBox):
            aerial_check_box.setChecked(False)

    # ======================== EXECUTE TOOL =============================================
    def setup_logging(self, current_config: dict[str, Any]):
        """Sets up log file and diagnostic window"""

        logger.handlers = []

        log_file_loc = current_config["FILE_PATHS"]["OUTPUT_DIR"]

        log_file_name = self._view.runId.text()
        file_handler = logging.FileHandler(f"{log_file_loc}\\{log_file_name}.log", "w")
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        file_handler.setLevel(logging.DEBUG)  # log file gets everything
        logger.addHandler(file_handler)

    def run_tool(self):
        """Runs the app date tool"""

        current_config: dict[str, Any] = self.generate_configuration_from_gui()
        self.setup_logging(current_config)

        # start algorithm thread and connect signals to slots
        self.adt_algo_worker = AdtAlgoThread(current_config)
        self.adt_algo_worker.start()
        self.adt_algo_worker.update_diagnostics.connect(self.update_diagnostic_window)
        self.adt_algo_worker.update_progress.connect(self.update_progress_bar)

    def update_diagnostic_window(self, val):
        """Append value to diagnostic window (QTextEdit widget)"""
        self._view.diagnosticWindow.append(val)

    def update_progress_bar(self, val):
        """Updates progress bar based on number of runs processed"""
        self._view.progressBar.setValue(val)

    # =====================================================================
    def _connect_signals(self):
        """Connects all signals to slots"""

        # fullfull menu actions
        self._view.actionOpen.triggered.connect(self.open_file)
        self._view.actionNewConfig.triggered.connect(self.new_config)
        self._view.actionSave.triggered.connect(self.save_file)
        self._view.actionSave_As.triggered.connect(self.save_file_as)
        self._view.actionAbout.triggered.connect(self.display_about_dialog)
        self._about.okayAbout.clicked.connect(self._about.reject)

        # use case
        self._view.useCaseComboBox.currentTextChanged.connect(self.update_use_case_description)
        self._view.useCaseComboBox.currentTextChanged.connect(self.deactivate_irrelavent_widgets)

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
        self._view.fileBrowseDRT.clicked.connect(
            partial(self.select_drt, self._view.agDriftReductionTableLocation, "(*.xlsx)")
        )
        self._view.fileBrowseScnDir.clicked.connect(partial(self.select_dir, self._view.scenarioFilesDirectoryLocation))
        self._view.fileBrowseIngrFateParams.clicked.connect(
            partial(self.select_file, self._view.pwcBatchFileLocation, "(*.csv)")
        )
        self._view.fileBrowseStateToHuc.clicked.connect(
            partial(self.select_file, self._view.fileBrowseStateToHuc, "(*.csv)")
        )
        self._view.fileBrowseBintoLandscapeParams.clicked.connect(
            partial(self.select_file, self._view.pwcBatchFileLocation, "(*.csv)")
        )

        self._view.agronomicPracticesTableLocation.editingFinished.connect(
            partial(self.get_xl_sheet_names, self._view.APTscenario, self._view.agronomicPracticesTableLocation)
        )
        self._view.agDriftReductionTableLocation.editingFinished.connect(
            partial(self.get_xl_sheet_names, self._view.DRTscenario, self._view.agDriftReductionTableLocation)
        )

        # bins
        self._view.bin1CheckBox.stateChanged.connect(partial(self.update_bin_display, self._view.bin1CheckBox, "1"))
        self._view.bin4CheckBox.stateChanged.connect(partial(self.update_bin_display, self._view.bin4CheckBox, "4"))
        self._view.bin7CheckBox.stateChanged.connect(partial(self.update_bin_display, self._view.bin7CheckBox, "7"))

        self._view.binSelectAll.clicked.connect(lambda: self._view.binsDisplaySelect.setText(Controller.ALL_BINS))
        self._view.binClearDisplay.clicked.connect(self.clear_bin_display)

        # app distances
        self._view.ground000m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground000m, "000m", "gd")
        )
        self._view.ground030m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground030m, "030m", "gd")
        )
        self._view.ground060m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground060m, "060m", "gd")
        )
        self._view.ground090m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground090m, "090m", "gd")
        )
        self._view.ground120m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground120m, "120m", "gd")
        )
        self._view.ground150m.stateChanged.connect(
            partial(self.update_app_display, self._view.ground150m, "150m", "gd")
        )

        self._view.groundClearDisplay.clicked.connect(self.clear_appdist_ground_selection)
        self._view.groundSelectAll.clicked.connect(
            lambda: self._view.groundDisplaySelect.setText(Controller.ALL_DISTANCES)
        )

        self._view.gran000m.stateChanged.connect(partial(self.update_app_display, self._view.gran000m, "000m", "gn"))
        self._view.gran030m.stateChanged.connect(partial(self.update_app_display, self._view.gran030m, "030m", "gn"))
        self._view.gran060m.stateChanged.connect(partial(self.update_app_display, self._view.gran060m, "060m", "gn"))
        self._view.gran090m.stateChanged.connect(partial(self.update_app_display, self._view.gran090m, "090m", "gn"))
        self._view.gran120m.stateChanged.connect(partial(self.update_app_display, self._view.gran120m, "120m", "gn"))
        self._view.gran150m.stateChanged.connect(partial(self.update_app_display, self._view.gran150m, "150m", "gn"))

        self._view.granularClearDisplay.clicked.connect(self.clear_appdist_gran_selection)
        self._view.granularSelectAll.clicked.connect(
            lambda: self._view.granDisplaySelect.setText(Controller.ALL_DISTANCES)
        )

        self._view.aerial000m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial000m, "000m", "ar")
        )
        self._view.aerial030m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial030m, "030m", "ar")
        )
        self._view.aerial060m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial060m, "060m", "ar")
        )
        self._view.aerial090m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial090m, "090m", "ar")
        )
        self._view.aerial120m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial120m, "120m", "ar")
        )
        self._view.aerial150m.stateChanged.connect(
            partial(self.update_app_display, self._view.aerial150m, "150m", "ar")
        )

        self._view.aerialClearDisplay.clicked.connect(self.clear_appdist_aerial_selection)
        self._view.aerialSelectAll.clicked.connect(
            lambda: self._view.aerialDisplaySelect.setText(Controller.ALL_DISTANCES)
        )

        # execute tool
        self._view.runButton.clicked.connect(self.run_tool)
