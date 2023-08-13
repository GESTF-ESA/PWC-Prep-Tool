"""Utility functions for the GUI"""

import pandas as pd
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLineEdit

from pwctool.constants import (
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    ALL_DEPTHS,
    FOLIAR_APPMETHOD,
    TBAND_APPMETHOD,
)


def get_xl_sheet_names(drop_down: QComboBox, text_widget: QLineEdit, error_dialog) -> None:
    """Gets the Excel sheet names for the APT or DRT and updates drop down"""

    file_path = text_widget.text()
    drop_down.clear()
    if file_path == "":
        drop_down.addItem("Specify file path before selecting")
    else:
        try:
            sheets: list = pd.ExcelFile(file_path).sheet_names
            drop_down.addItems(sheets)
        except (AssertionError, OSError, FileNotFoundError):
            error_dialog.errMsgLabel.setText(
                "The path may be incorrect for the Agronomic Practices Table or Drift Reducation Table."
            )
            error_dialog.exec_()


def enable_application_methods(view, app_method: int) -> None:
    """Enables application methods items"""

    appmeth_title = getattr(view, f"appmeth{app_method}Title")
    appmeth_desc = getattr(view, f"appmeth{app_method}Desc")
    appmeth_distancelabel = getattr(view, f"appmeth{app_method}distancelabel")
    appmeth_selectalldistances = getattr(view, f"appmeth{app_method}_selectalldistances")
    appmeth_clearalldistances = getattr(view, f"appmeth{app_method}_clearalldistances")

    appmeth_title.setStyleSheet("")
    appmeth_desc.setStyleSheet("")

    appmeth_distancelabel.setStyleSheet("")
    appmeth_selectalldistances.setStyleSheet("")
    appmeth_selectalldistances.setEnabled(True)
    appmeth_clearalldistances.setStyleSheet("")
    appmeth_clearalldistances.setEnabled(True)
    for distance in ALL_DISTANCES:
        getattr(view, f"appmeth{app_method}_{distance}").setStyleSheet("")
        getattr(view, f"appmeth{app_method}_{distance}").setEnabled(True)

    if app_method in BURIED_APPMETHODS:
        getattr(view, f"appmeth{app_method}DepthLabel").setStyleSheet("")
        getattr(view, f"appmeth{app_method}_selectalldepths").setStyleSheet("")
        getattr(view, f"appmeth{app_method}_selectalldepths").setEnabled(True)
        getattr(view, f"appmeth{app_method}_clearalldepths").setStyleSheet("")
        getattr(view, f"appmeth{app_method}_clearalldepths").setEnabled(True)

        if app_method == TBAND_APPMETHOD:
            view.tbandSplitLabel.setStyleSheet("")
            view.appmeth5_tbandsplitfrac.setEnabled(True)
            view.appmeth5_tbandsplitfrac.setStyleSheet("")
            view.tbandSplitDesc.setStyleSheet("")
            for depth in [4, 6, 8, 10, 12]:  # no depth of 2 cm for tband
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet("")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(True)

        else:
            for depth in ALL_DEPTHS:
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet("")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(True)

    if app_method == FOLIAR_APPMETHOD:
        getattr(view, f"appmeth{app_method}DriftOnlyLabel").setStyleSheet("")
        for distance in ALL_DISTANCES:
            getattr(view, f"appmeth{app_method}_{distance}_driftonly").setEnabled(True)
        view.applicationsTabDesc2.setStyleSheet("")


def disable_application_methods(view, app_method) -> None:
    """Disables application methods items"""

    appmeth_title = getattr(view, f"appmeth{app_method}Title")
    appmeth_desc = getattr(view, f"appmeth{app_method}Desc")
    appmeth_distancelabel = getattr(view, f"appmeth{app_method}distancelabel")
    appmeth_selectalldistances = getattr(view, f"appmeth{app_method}_selectalldistances")
    appmeth_clearalldistances = getattr(view, f"appmeth{app_method}_clearalldistances")

    appmeth_title.setStyleSheet("color:grey")
    appmeth_desc.setStyleSheet("color:grey")

    appmeth_distancelabel.setStyleSheet("color:grey")
    appmeth_selectalldistances.setStyleSheet("color:grey")
    appmeth_selectalldistances.setEnabled(False)
    appmeth_clearalldistances.setStyleSheet("color:grey")
    appmeth_clearalldistances.setEnabled(False)
    for distance in ALL_DISTANCES:
        getattr(view, f"appmeth{app_method}_{distance}").setStyleSheet("color:grey")
        getattr(view, f"appmeth{app_method}_{distance}").setEnabled(False)

    if app_method in BURIED_APPMETHODS:
        getattr(view, f"appmeth{app_method}DepthLabel").setStyleSheet("color:grey")
        getattr(view, f"appmeth{app_method}_selectalldepths").setStyleSheet("color:grey")
        getattr(view, f"appmeth{app_method}_selectalldepths").setEnabled(False)
        getattr(view, f"appmeth{app_method}_clearalldepths").setStyleSheet("color:grey")
        getattr(view, f"appmeth{app_method}_clearalldepths").setEnabled(False)

        if app_method == TBAND_APPMETHOD:
            view.tbandSplitLabel.setStyleSheet("color:grey")
            view.appmeth5_tbandsplitfrac.setEnabled(False)
            view.appmeth5_tbandsplitfrac.setStyleSheet("color:grey")
            view.tbandSplitDesc.setStyleSheet("color:grey")
            for depth in [4, 6, 8, 10, 12]:  # no depth of 2 cm for tband
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet("color:grey")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(False)

        else:
            for depth in ALL_DEPTHS:
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setStyleSheet("color:grey")
                getattr(view, f"appmeth{app_method}_depth{depth}cm").setEnabled(False)

    if app_method == FOLIAR_APPMETHOD:
        getattr(view, f"appmeth{app_method}DriftOnlyLabel").setStyleSheet("color:grey")
        for distance in ALL_DISTANCES:
            getattr(view, f"appmeth{app_method}_{distance}_driftonly").setEnabled(False)
        view.applicationsTabDesc2.setStyleSheet("color:grey")


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
            enable_application_methods(view, i)
        else:
            disable_application_methods(view, i)
