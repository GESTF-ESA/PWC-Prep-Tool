"""
Initializes the GUI with information from a config file
"""

from typing import Any
import pandas as pd
from PyQt5.QtWidgets import QCheckBox, QComboBox, QWidget, QDialog, QLineEdit

from pwctool.constants import (
    ALL_BINS,
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    ALL_DEPTHS,
    FOLIAR_APPMETHOD,
    TBAND_APPMETHOD,
)


def init_gui_settings_from_config(view: QWidget, config: dict[str, Any], error_dialog: QDialog) -> None:
    """Sets the GUI settings based on the values in the config file"""

    _init_assessment_widgets(view, config)
    _init_file_paths(view, config)
    _init_gui_options(view, config, error_dialog)
    _init_aquatic_bins(view, config)
    _init_application_methods(view, config)

    # Reset the progress bar
    view.progressBar.setValue(0)


def _init_assessment_widgets(view, config: dict[str, Any]) -> None:
    """Sets the assessment widgets"""

    if config["ASSESSMENT_TYPE"] == "fifra":
        view.fifraRadButton.setChecked(True)
    else:
        view.esaRadButton.setChecked(True)


def _init_file_paths(view: QWidget, config: dict[str, Any]) -> None:
    """Sets the file paths in the GUI"""

    file_path_mappings = {
        "PWC_BATCH_CSV": view.pwcBatchFileLocation,
        "OUTPUT_DIR": view.outputFileDirLocation,
        "WETTEST_MONTH_CSV": view.wettestMonthTableLocation,
        "AGRONOMIC_PRACTICES_EXCEL": view.agronomicPracticesTableLocation,
        "SCENARIO_FILES_PATH": view.scenarioFilesDirectoryLocation,
        "AGDRIFT_REDUCTION_TABLE": view.agDriftReductionTableLocation,
        "INGR_FATE_PARAMS": view.ingrFateParamsLocation,
    }
    for name, qline_edit in file_path_mappings.items():
        file_path = config.get("FILE_PATHS", {}).get(name)
        qline_edit.setText(file_path)


def _init_gui_options(view: QWidget, config: dict[str, Any], error_dialog) -> None:
    """Sets the GUI settings based on the values in the config file"""

    setting_mappings = {
        "RUN_ID": view.runId,
        "USE_CASE": view.useCaseComboBox,
        "APT_SCENARIO": view.APTscenario,
        "DRT_SCENARIO": view.DRTscenario,
        "RANDOM_START_DATES": view.randomStartDatesBool,
        "RANDOM_SEED": view.randomSeed,
        "DATE_PRIORITIZATION": view.datePriorComboBox,
        "RESIDENTIAL_ADJ_FACTOR": view.resADJFactor,
        "WETMONTH_PRIORITIZATION": view.wettestMonthPrior,
    }

    for setting, gui_widget in setting_mappings.items():
        setting_value: str = config.get(setting)
        if isinstance(gui_widget, QComboBox):
            if gui_widget.findText(setting_value) == -1:  # setting_value not in combo box list
                if setting == "APT_SCENARIO":
                    if view.agronomicPracticesTableLocation.text() == "":
                        gui_widget.clear()
                        gui_widget.addItem(setting_value)
                    else:
                        get_xl_sheet_names(gui_widget, view.agronomicPracticesTableLocation, error_dialog, "APT")
                elif setting == "DRT_SCENARIO":
                    if view.agDriftReductionTableLocation.text() == "":
                        gui_widget.clear()
                        gui_widget.addItem(setting_value)
                    else:
                        get_xl_sheet_names(gui_widget, view.agDriftReductionTableLocation, error_dialog, "DRT")
            gui_widget.setCurrentText(setting_value)
        elif isinstance(gui_widget, QCheckBox):
            gui_widget.setChecked(setting_value)
        else:
            gui_widget.setText(str(setting_value))


def _init_aquatic_bins(view: QWidget, config: dict[str, Any]) -> None:
    """Sets the aquatic bin selection in the GUI"""

    for bin_number in ALL_BINS:
        bin_value_bool = config.get("BINS", {}).get(bin_number)
        if config["ASSESSMENT_TYPE"] == "fifra":
            getattr(view, f"bin{bin_number}CheckBoxFIFRA").setChecked(bin_value_bool)
        else:
            getattr(view, f"bin{bin_number}CheckBoxESA").setChecked(bin_value_bool)


def _init_application_methods(view: QWidget, config: dict[str, Any]) -> None:
    """Sets the application method selection in the GUI"""

    for app_method in ALL_APPMETHODS:
        # Buried application methods (3 - 7) have depths
        if app_method in BURIED_APPMETHODS:
            # TBand-Split application method (5) has unique parameter for tband-split fraction
            if app_method == TBAND_APPMETHOD:
                tband_split_fraction = config["APPMETH5_TBANDFRAC"]
                view.appmeth5_tbandsplitfrac.setText(str(tband_split_fraction))
                for depth in [4, 6, 8, 10, 12]:
                    appmeth_depth_bool = config.get(f"APPMETH{app_method}_DEPTHS", {}).get(depth, False)
                    getattr(view, f"appmeth{app_method}_depth{depth}cm").setChecked(appmeth_depth_bool)
            else:
                for depth in ALL_DEPTHS:
                    appmeth_depth_bool = config.get(f"APPMETH{app_method}_DEPTHS", {}).get(depth, False)
                    getattr(view, f"appmeth{app_method}_depth{depth}cm").setChecked(appmeth_depth_bool)

        else:  # app method 1 (bare ground) and 2 (foliar)
            for distance in ALL_DISTANCES:
                appmeth_distance = config.get(f"APPMETH{app_method}_DISTANCES", {}).get(distance)
                getattr(view, f"appmeth{app_method}_{distance}").setChecked(appmeth_distance)
            # Handle special case of foliar application method (2) having both standard and drift only options
            if app_method == FOLIAR_APPMETHOD:
                for distance in ALL_DISTANCES:
                    appmeth_driftonly_distance_bool = config.get(f"APPMETH{app_method}_DRIFT_ONLY", {}).get(distance)
                    getattr(view, f"appmeth{app_method}_{distance}_driftonly").setChecked(
                        appmeth_driftonly_distance_bool
                    )


def get_xl_sheet_names(drop_down: QComboBox, text_widget: QLineEdit, error_dialog: QDialog, table: str) -> None:
    """Gets the Excel sheet names for the APT or DRT and updates drop down"""

    fnf_error_messages = {
        "APT": "Invalid Agronomic Practices Table path, please correct and try again.",
        "DRT": "Invalid Drift Reduction Table path, please correct and try again.",
    }

    pm_error_messages = {
        "APT": "Please close the Agronomic Practices Table before loading a configuration to avoid permission error and try again.",
        "DRT": "Please close the Drift Reduction Table before loading a configuration to avoid permission error and try again.",
    }

    file_path = text_widget.text()
    drop_down.clear()
    if file_path == "":
        drop_down.addItem("Specify file path before selecting")
    else:
        try:
            sheets: list = pd.ExcelFile(file_path).sheet_names
        except FileNotFoundError:
            error_dialog.errMsgLabel.setText(fnf_error_messages.get(table, "Unknown Table"))
            error_dialog.exec_()
        except PermissionError:  # this happens when apt/drt is open when user loads a config
            error_dialog.errMsgLabel.setText(pm_error_messages.get(table, "Unknown Table"))
            error_dialog.exec_()
        else:
            drop_down.addItems(sheets)
