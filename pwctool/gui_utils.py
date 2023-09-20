"""Utility functions for the GUI"""

import pandas as pd
from PyQt5.QtWidgets import QComboBox, QDialog, QLineEdit

from pwctool.constants import (
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    ALL_DEPTHS,
    FOLIAR_APPMETHOD,
    TBAND_APPMETHOD,
)


def enable_disable_wettest_month_table(view):
    """Enables and disables the wettest month file location based on wettest
    month checkbox"""

    if view.wettestMonthPrior.isChecked():
        view.wettestMonthTableLabel.setStyleSheet("color:black")
        view.wettestMonthTableLocation.setEnabled(True)
        view.fileBrowseWettestMonthTable.setEnabled(True)
        view.fileBrowseWettestMonthTable.setStyleSheet("color:black")

    else:
        view.wettestMonthTableLabel.setStyleSheet("color:grey")
        view.wettestMonthTableLocation.setEnabled(False)
        view.fileBrowseWettestMonthTable.setEnabled(False)
        view.fileBrowseWettestMonthTable.setStyleSheet("color:grey")


def enable_disable_assessment_type(view):
    """Enables and disables widgets based on assessment type selection"""

    if view.fifraRadButton.isChecked():

        # scenario/hucs
        view.newScnHucRadButton.setChecked(True)
        view.legacyScnHucRadButton.setEnabled(False)
        view.legacyScnHucRadButton.setStyleSheet("color:grey")

        # waterbodies
        view.fifraWBLabel.setStyleSheet("color:black")
        view.fifraWBSelectAll.setEnabled(True)
        view.fifraWBClearAll.setEnabled(True)
        view.bin4CheckBoxFIFRA.setEnabled(True)
        view.bin7CheckBoxFIFRA.setEnabled(True)
        view.bin10CheckBoxFIFRA.setEnabled(True)

        view.binLabel.setStyleSheet("color:grey")
        view.binSelectAll.setEnabled(False)
        view.binClearAll.setEnabled(False)
        view.bin4CheckBoxESA.setEnabled(False)
        view.bin7CheckBoxESA.setEnabled(False)
        view.bin10CheckBoxESA.setEnabled(False)

    if view.esaRadButton.isChecked():

        # scenario/hucs
        view.legacyScnHucRadButton.setEnabled(True)
        view.legacyScnHucRadButton.setStyleSheet("color:black")

        # waterbodies
        view.fifraWBLabel.setStyleSheet("color:grey")
        view.fifraWBSelectAll.setEnabled(False)
        view.fifraWBClearAll.setEnabled(False)
        view.bin4CheckBoxFIFRA.setEnabled(False)
        view.bin7CheckBoxFIFRA.setEnabled(False)
        view.bin10CheckBoxFIFRA.setEnabled(False)

        view.binLabel.setStyleSheet("color:black")
        view.binSelectAll.setEnabled(True)
        view.binClearAll.setEnabled(True)
        view.bin4CheckBoxESA.setEnabled(True)
        view.bin7CheckBoxESA.setEnabled(True)
        view.bin10CheckBoxESA.setEnabled(True)


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


def enable_disable_app_methods(view, app_method: int, enable_disable_flag: bool) -> None:
    """Enables or disables application method widgets and descriptions"""

    if enable_disable_flag:
        color = "black"
    else:
        color = "grey"

    appmeth_title = getattr(view, f"appmeth{app_method}Title")
    appmeth_title.setStyleSheet(f"color:{color}")

    appmeth_desc = getattr(view, f"appmeth{app_method}Desc")
    appmeth_desc.setStyleSheet(f"color:{color}")

    if app_method in BURIED_APPMETHODS:
        getattr(view, f"appmeth{app_method}DepthLabel").setStyleSheet(f"color:{color}")
        getattr(view, f"appmeth{app_method}_selectalldepths").setStyleSheet(f"color:{color}")
        getattr(view, f"appmeth{app_method}_selectalldepths").setEnabled(enable_disable_flag)
        getattr(view, f"appmeth{app_method}_clearalldepths").setStyleSheet(f"color:{color}")
        getattr(view, f"appmeth{app_method}_clearalldepths").setEnabled(enable_disable_flag)

        if app_method == TBAND_APPMETHOD:
            view.tbandSplitLabel.setStyleSheet(f"color:{color}")
            view.appmeth5_tbandsplitfrac.setEnabled(enable_disable_flag)
            view.appmeth5_tbandsplitfrac.setStyleSheet(f"color:{color}")
            view.tbandSplitDesc.setStyleSheet(f"color:{color}")
            for depth in [4, 6, 8, 10, 12]:  # no depth of 2 cm for tband
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet(f"color:{color}")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(enable_disable_flag)

        else:
            for depth in ALL_DEPTHS:
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet(f"color:{color}")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(enable_disable_flag)

    else:  # application methods 1 (bare ground) and 2 (aerial)
        # enable distance related widgets
        appmeth_distancelabel = getattr(view, f"appmeth{app_method}distancelabel")
        appmeth_distancelabel.setStyleSheet(f"color:{color}")

        appmeth_selectalldistances = getattr(view, f"appmeth{app_method}_selectalldistances")
        appmeth_selectalldistances.setStyleSheet(f"color:{color}")
        appmeth_selectalldistances.setEnabled(enable_disable_flag)

        appmeth_clearalldistances = getattr(view, f"appmeth{app_method}_clearalldistances")
        appmeth_clearalldistances.setStyleSheet(f"color:{color}")
        appmeth_clearalldistances.setEnabled(enable_disable_flag)

        for distance in ALL_DISTANCES:
            getattr(view, f"appmeth{app_method}_{distance}").setStyleSheet(f"color:{color}")
            getattr(view, f"appmeth{app_method}_{distance}").setEnabled(enable_disable_flag)

    if app_method == FOLIAR_APPMETHOD:
        getattr(view, f"appmeth{app_method}DriftOnlyLabel").setStyleSheet(f"color:{color}")
        for distance in ALL_DISTANCES:
            getattr(view, f"appmeth{app_method}_{distance}_driftonly").setEnabled(enable_disable_flag)
        view.applicationsTabDesc2.setStyleSheet(f"color:{color}")


def restrict_application_methods(view) -> None:
    """Restricts the application method tabs based on presence in APT"""

    try:
        ag_practices_table: pd.DataFrame = pd.read_excel(
            view.agronomicPracticesTableLocation.text(), sheet_name=view.APTscenario.currentText()
        )
    except (AssertionError, FileNotFoundError, OSError):
        return None

    app_methods_to_enable: list[int] = ag_practices_table["ApplicationMethod"].unique().tolist()

    for i in ALL_APPMETHODS:
        if i in app_methods_to_enable:
            enable_disable_app_methods(view, i, True)
        else:
            enable_disable_app_methods(view, i, False)
