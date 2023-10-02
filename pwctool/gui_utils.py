"""Utility functions for the GUI"""

import pandas as pd
from typing import Any
from PyQt5.QtWidgets import QDialog, QWidget

from pwctool.constants import (
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    ALL_DEPTHS,
    FOLIAR_APPMETHOD,
    TBAND_APPMETHOD,
    USE_CASE_DESCRIPTION,
)
from pwctool.config_loader import init_gui_settings_from_config


def create_blank_config(use_case: str):
    """Creates a blank configuration"""

    # create a new blank configuration
    config: dict[str, Any] = {}
    config["USE_CASE"] = use_case

    config["ASSESSMENT_TYPE"] = "fifra"

    config["FILE_PATHS"] = {}
    config["FILE_PATHS"]["PWC_BATCH_CSV"] = ""
    config["FILE_PATHS"]["OUTPUT_DIR"] = ""
    config["FILE_PATHS"]["WETTEST_MONTH_CSV"] = ""
    config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"] = ""
    config["FILE_PATHS"]["SCENARIO_FILES_PATH"] = ""
    config["FILE_PATHS"]["INGR_FATE_PARAMS"] = ""
    config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"] = ""
    config["FILE_PATHS"]["BIN_TO_LANDSCAPE"] = ""

    config["BINS"] = {}
    config["BINS"][4] = False
    config["BINS"][7] = False
    config["BINS"][10] = False

    for app_method in ALL_APPMETHODS:

        if app_method in BURIED_APPMETHODS:
            if app_method == TBAND_APPMETHOD:
                config["APPMETH5_DEPTHS"] = {}
                config["APPMETH5_DEPTHS"][4] = False
                config["APPMETH5_DEPTHS"][6] = False
                config["APPMETH5_DEPTHS"][8] = False
                config["APPMETH5_DEPTHS"][10] = False
                config["APPMETH5_DEPTHS"][12] = False

                config["APPMETH5_TBANDFRAC"] = 0.5

            else:
                config[f"APPMETH{app_method}_DEPTHS"] = {}
                for depth in ALL_DEPTHS:
                    config[f"APPMETH{app_method}_DEPTHS"][depth] = False

        else:  # app method 1 (bare ground) and 2 (foliar)
            config[f"APPMETH{app_method}_DISTANCES"] = {}
            for distance in ALL_DISTANCES:
                config[f"APPMETH{app_method}_DISTANCES"][distance] = False

            if app_method == FOLIAR_APPMETHOD:
                config["APPMETH2_DRIFT_ONLY"] = {}
                config["APPMETH2_DRIFT_ONLY"] = {
                    "000m": False,
                    "030m": False,
                    "060m": False,
                    "090m": False,
                    "120m": False,
                    "150m": False,
                }

    config["APT_SCENARIO"] = "Specify file path before selecting"
    config["DRT_SCENARIO"] = "Specify file path before selecting"
    config["RESIDENTIAL_ADJ_FACTOR"] = 0.587
    config["RANDOM_START_DATES"] = False
    config["RANDOM_SEED"] = ""
    config["RUN_ID"] = ""
    config["DATE_PRIORITIZATION"] = ""
    config["WETMONTH_PRIORITIZATION"] = True

    return config


def update_gui_usecase_change(view: QWidget, error_dialog: QDialog):
    """Updates the use case description when a new use case is selected"""
    new_use_case = view.useCaseComboBox.currentText()
    view.useCaseLabel.setText(USE_CASE_DESCRIPTION[new_use_case])

    blank_config = create_blank_config(new_use_case)
    init_gui_settings_from_config(view, blank_config, error_dialog)
    _activate_all_widgets(view)
    _enable_disable_widgets_usechange(view, new_use_case)


def _enable_disable_widgets_usechange(view: QWidget, new_use_case: str):
    """Deactivates widgets that are not relavent for the use case."""

    if new_use_case == "Use Case #1":
        # disable source batch file parameter
        view.pwcBatchFileLocation.setEnabled(False)
        view.pwcBatchFileLabel.setStyleSheet("color: grey")
        view.fileBrowseSourcePWCBatch.setEnabled(False)

    else:  # use case 2
        # disable wettest month widgets
        view.wettestMonthTableLocation.setEnabled(False)
        view.fileBrowseWettestMonthTable.setStyleSheet("color: grey")
        view.fileBrowseWettestMonthTable.setEnabled(False)
        view.wettestMonthTableLabel.setStyleSheet("color: grey")

        # disable tables
        view.ingrFateParamsLocation.setEnabled(False)
        view.fileBrowseIngrFateParams.setStyleSheet("color: grey")
        view.fileBrowseIngrFateParams.setEnabled(False)
        view.ingrFateParamsLabel.setStyleSheet("color: grey")

        # disable waterbody widgets
        view.binsParamDescription.setStyleSheet("color: grey")
        view.binsParamDescription2.setStyleSheet("color: grey")
        view.binLabel.setStyleSheet("color:grey")
        view.binSelectAll.setEnabled(False)
        view.binClearAll.setEnabled(False)
        view.bin4CheckBoxESA.setEnabled(False)
        view.bin7CheckBoxESA.setEnabled(False)
        view.bin10CheckBoxESA.setEnabled(False)

        view.fifraWBLabel.setStyleSheet("color:grey")
        view.fifraWBSelectAll.setEnabled(False)
        view.fifraWBClearAll.setEnabled(False)
        view.bin4CheckBoxFIFRA.setEnabled(False)
        view.bin7CheckBoxFIFRA.setEnabled(False)
        view.bin10CheckBoxFIFRA.setEnabled(False)

        # disable app distances tab
        view.applicationsTabDesc1.setStyleSheet("color: grey")
        view.applicationsTabDesc3.setStyleSheet("color: grey")
        view.applicationsTabDesc4.setStyleSheet("color: grey")
        view.applicationsTabs.setStyleSheet("color: grey")

        # disable app method items
        for i in ALL_APPMETHODS:
            enable_disable_app_methods(view, i, False)

        # date assignment parameters
        view.wettestMonthPrior.setEnabled(False)
        view.wettestMonthDesc.setStyleSheet("color:grey")
        view.wettestMonthPriorLable.setStyleSheet("color: grey")

        view.datePriorComboBox.setEnabled(False)
        view.datePriorDesc.setStyleSheet("color:grey")
        view.datePriorLabel.setStyleSheet("color: grey")

        view.randomStartDatesBool.setEnabled(False)
        view.randomSeed.setEnabled(False)
        view.randomDateDesc.setStyleSheet("color:grey")
        view.randomDateLabel.setStyleSheet("color:grey")
        view.randomSeedLabel.setStyleSheet("color: grey")

        # disable assessment tab widgets
        view.fifraRadButton.setEnabled(False)
        view.fifraRadButton.setStyleSheet("color:grey")
        view.esaRadButton.setEnabled(False)
        view.esaRadButton.setStyleSheet("color:grey")

        view.assessmentTypeLabel.setStyleSheet("color:grey")
        view.assessmentDesc.setStyleSheet("color:grey")
        view.assessmentDesc2.setStyleSheet("color:grey")

        # residential ADJ factor
        view.resADJFactorLabel.setStyleSheet("color: grey")
        view.redADJFactDesc.setStyleSheet("color: grey")
        view.resADJFactor.setEnabled(False)


def _activate_all_widgets(view: QWidget):
    """Enables all widgets and resets styles"""
    # enable app methods items
    for i in ALL_APPMETHODS:
        enable_disable_app_methods(view, i, True)
    # enable source batch file parameter
    view.pwcBatchFileLocation.setEnabled(True)
    view.pwcBatchFileLabel.setStyleSheet("color: black")
    view.fileBrowseSourcePWCBatch.setEnabled(True)
    # enable assessment tab widgets
    view.fifraRadButton.setEnabled(True)
    view.fifraRadButton.setStyleSheet("color:black")
    view.esaRadButton.setEnabled(True)
    view.esaRadButton.setStyleSheet("color:black")
    view.assessmentTypeLabel.setStyleSheet("color:black")
    view.assessmentDesc.setStyleSheet("color:black")
    view.assessmentDesc2.setStyleSheet("color:black")
    # other tables
    view.wettestMonthTableLocation.setEnabled(True)
    view.fileBrowseWettestMonthTable.setStyleSheet("color: black")
    view.fileBrowseWettestMonthTable.setEnabled(True)
    view.wettestMonthTableLabel.setStyleSheet("color: black")
    view.ingrFateParamsLocation.setEnabled(True)
    view.fileBrowseIngrFateParams.setStyleSheet("color: black")
    view.fileBrowseIngrFateParams.setEnabled(True)
    view.ingrFateParamsLabel.setStyleSheet("color: black")
    # enable waterbody widgets
    view.binsParamDescription.setStyleSheet("color: black")
    view.binsParamDescription2.setStyleSheet("color: black")
    view.binLabel.setStyleSheet("color:black")
    view.binSelectAll.setEnabled(True)
    view.binClearAll.setEnabled(True)
    view.bin4CheckBoxESA.setEnabled(True)
    view.bin7CheckBoxESA.setEnabled(True)
    view.bin10CheckBoxESA.setEnabled(True)
    view.fifraWBLabel.setStyleSheet("color:black")
    view.fifraWBSelectAll.setEnabled(True)
    view.fifraWBClearAll.setEnabled(True)
    view.bin4CheckBoxFIFRA.setEnabled(True)
    view.bin7CheckBoxFIFRA.setEnabled(True)
    view.bin10CheckBoxFIFRA.setEnabled(True)
    # enable app distances tab
    view.applicationsTabDesc1.setStyleSheet("color: black")
    view.applicationsTabDesc3.setStyleSheet("color: black")
    view.applicationsTabDesc4.setStyleSheet("color: black")
    view.applicationsTabs.setStyleSheet("color: black")
    # date assignment parameters
    view.wettestMonthPrior.setEnabled(True)
    view.wettestMonthDesc.setStyleSheet("color: black")
    view.wettestMonthPriorLable.setStyleSheet("color: black")
    view.datePriorComboBox.setEnabled(True)
    view.datePriorDesc.setStyleSheet("color: black")
    view.datePriorLabel.setStyleSheet("color: black")
    view.randomStartDatesBool.setEnabled(True)
    view.randomSeed.setEnabled(True)
    view.randomDateDesc.setStyleSheet("color: black")
    view.randomDateLabel.setStyleSheet("color: black")
    view.randomSeedLabel.setStyleSheet("color: black")
    # residential ADJ factor
    view.resADJFactorLabel.setStyleSheet("color: black")
    view.redADJFactDesc.setStyleSheet("color: black")
    view.resADJFactor.setEnabled(True)


def enable_disable_waterbodies(view: QWidget):
    """Enables and disables waterbody params based on assessment type selection"""

    if view.fifraRadButton.isChecked():
        esa_bool: bool = False
        fifra_bool: bool = True
        esa_style: str = "grey"
        fifra_style: str = "black"

    else:
        esa_bool: bool = True
        fifra_bool: bool = False
        esa_style: str = "black"
        fifra_style: str = "grey"

    # enable/disable fifra waterbodies
    view.fifraWBLabel.setStyleSheet(f"color:{fifra_style}")

    view.fifraWBSelectAll.setEnabled(fifra_bool)
    view.fifraWBSelectAll.setStyleSheet(f"color:{fifra_style}")
    view.fifraWBClearAll.setEnabled(fifra_bool)
    view.fifraWBClearAll.setStyleSheet(f"color:{fifra_style}")

    view.bin4CheckBoxFIFRA.setEnabled(fifra_bool)
    view.bin4CheckBoxFIFRA.setChecked(fifra_bool)
    view.bin7CheckBoxFIFRA.setEnabled(fifra_bool)
    view.bin7CheckBoxFIFRA.setChecked(fifra_bool)
    view.bin10CheckBoxFIFRA.setEnabled(fifra_bool)
    view.bin10CheckBoxFIFRA.setChecked(fifra_bool)

    # enable/disable esa waterbodies
    view.binLabel.setStyleSheet(f"color:{esa_style}")

    view.binSelectAll.setEnabled(esa_bool)
    view.binSelectAll.setStyleSheet(f"color:{esa_style}")
    view.binClearAll.setEnabled(esa_bool)
    view.binClearAll.setStyleSheet(f"color:{esa_style}")

    view.bin4CheckBoxESA.setEnabled(esa_bool)
    view.bin4CheckBoxESA.setChecked(esa_bool)
    view.bin7CheckBoxESA.setEnabled(esa_bool)
    view.bin7CheckBoxESA.setChecked(esa_bool)
    view.bin10CheckBoxESA.setEnabled(esa_bool)
    view.bin10CheckBoxESA.setChecked(esa_bool)


def enable_disable_wettest_month_prior(view: QWidget):
    """Enables and dissables wettest month prioritization based on assessment type"""

    if view.fifraRadButton.isChecked():
        view.wettestMonthPrior.setEnabled(False)
        view.wettestMonthPrior.setChecked(False)
        view.wettestMonthPriorLable.setStyleSheet("color:grey")
        view.wettestMonthDesc.setStyleSheet("color:grey")
    else:
        view.wettestMonthPrior.setEnabled(True)
        view.wettestMonthPrior.setChecked(True)
        view.wettestMonthPriorLable.setStyleSheet("color:black")
        view.wettestMonthDesc.setStyleSheet("color:black")

    enable_disable_wettest_month_table(view)


def enable_disable_wettest_month_table(view: QWidget):
    """Enables and disables the wettest month file location based on wettest
    month checkbox. Wettest month prioritization is only valid for ESA runs"""

    bool_val = False
    style = "grey"

    if view.esaRadButton.isChecked():
        if view.wettestMonthPrior.isChecked():
            bool_val = True
            style = "black"

    # enable/disable wettest month widgets in file locations
    view.wettestMonthTableLabel.setStyleSheet(f"color:{style}")
    view.wettestMonthTableLocation.setText("")
    view.wettestMonthTableLocation.setEnabled(bool_val)
    view.fileBrowseWettestMonthTable.setEnabled(bool_val)
    view.fileBrowseWettestMonthTable.setStyleSheet(f"color:{style}")

    # enable/disable application date prioritization
    view.datePriorLabel.setStyleSheet(f"color:{style}")
    view.datePriorComboBox.setStyleSheet(f"color:{style}")
    view.datePriorComboBox.setEnabled(bool_val)
    view.datePriorDesc.setStyleSheet(f"color:{style}")


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

    if view.useCaseComboBox.currentText() == "Use Case #2":
        return None

    try:
        ag_practices_table: pd.DataFrame = pd.read_excel(
            view.agronomicPracticesTableLocation.text(), sheet_name=view.APTscenario.currentText()
        )
    except (AssertionError, FileNotFoundError, OSError, ValueError):
        # if issue getting file, enable all app method widgets
        for i in ALL_APPMETHODS:
            enable_disable_app_methods(view, i, True)
        return None

    app_methods_to_enable: list[int] = ag_practices_table["ApplicationMethod"].unique().tolist()

    for i in ALL_APPMETHODS:
        if i in app_methods_to_enable:
            enable_disable_app_methods(view, i, True)
        else:
            enable_disable_app_methods(view, i, False)
