"""Writes a config file based on the current settings in the GUI"""

from typing import Any
from pwctool.constants import (
    ALL_BINS,
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    ALL_DEPTHS,
    FOLIAR_APPMETHOD,
    TBAND_APPMETHOD,
)


def generate_configuration_from_gui(view) -> dict[str, Any]:
    """Generates a configuration dictionary from the GUI settings and returns it."""

    config: dict[str, Any] = {
        "RUN_ID": view.runId.text(),
        "USE_CASE": view.useCaseComboBox.currentText(),
        "FILE_PATHS": {
            "PWC_BATCH_CSV": view.pwcBatchFileLocation.text(),
            "OUTPUT_DIR": view.outputFileDirLocation.text(),
            "WETTEST_MONTH_CSV": view.wettestMonthTableLocation.text(),
            "AGRONOMIC_PRACTICES_EXCEL": view.agronomicPracticesTableLocation.text(),
            "AGDRIFT_REDUCTION_TABLE": view.agDriftReductionTableLocation.text(),
            "INGR_FATE_PARAMS": view.ingrFateParamsLocation.text(),
        },
        "APT_SCENARIO": view.APTscenario.currentText(),
        "DRT_SCENARIO": view.DRTscenario.currentText(),
        "RANDOM_START_DATES": view.randomStartDatesBool.isChecked(),
        "RANDOM_SEED": view.randomSeed.text(),
        "DATE_PRIORITIZATION": view.datePriorComboBox.currentText(),
        "WETMONTH_PRIORITIZATION": view.wettestMonthPrior.isChecked(),
    }

    _add_assessment_settings(config, view)
    _add_residential_adjustment_factor(config, view)
    _add_bin_settings(config, view)
    _add_appmeth_settings(config, view)

    return config


def _add_residential_adjustment_factor(config: dict[str, Any], view) -> None:
    """Adds the residential adjustment factor to the config dictionary."""

    try:
        config["RESIDENTIAL_ADJ_FACTOR"] = float(view.resADJFactor.text())
    except ValueError:
        config["RESIDENTIAL_ADJ_FACTOR"] = 0.0


def _add_bin_settings(config: dict[str, Any], view) -> None:
    """Adds the bin settings to the config dictionary."""

    config["BINS"] = {}
    for bin_number in ALL_BINS:
        if config["ASSESSMENT_TYPE"] == "fifra":
            config["BINS"][bin_number] = getattr(view, f"bin{bin_number}CheckBoxFIFRA").isChecked()
        else:
            config["BINS"][bin_number] = getattr(view, f"bin{bin_number}CheckBoxESA").isChecked()


def _add_appmeth_settings(config: dict[str, Any], view) -> None:
    """Adds the appmeth settings to the config dictionary.
    There are seven application methods, with methods 1 and 2 not using depth."""

    for method_num in ALL_APPMETHODS:

        # Application methods 3-7 have depth settings
        if method_num in BURIED_APPMETHODS:
            config[f"APPMETH{method_num}_DEPTHS"] = {}
            if method_num == TBAND_APPMETHOD:
                for depth in [4, 6, 8, 10, 12]:
                    config[f"APPMETH{method_num}_DEPTHS"][depth] = getattr(
                        view, f"appmeth{method_num}_depth{depth}cm"
                    ).isChecked()
                # Method 5 has a unique parameter for tband-split fraction
                # TODO: Add a check to the GUI forcing user to enter a float for this value so we don't need a try/except here
                try:
                    config["APPMETH5_TBANDFRAC"] = float(view.appmeth5_tbandsplitfrac.text())
                except ValueError:
                    config["APPMETH5_TBANDFRAC"] = 0.0
                #     self.error_dialog.errMsgLabel.setText(
                #         "The App. Method 5 tband-split fraction may not be entered as a decimal. Please ensure it is."
                #     )
                # self.error_dialog.exec_()
            else:
                for depth in ALL_DEPTHS:
                    config[f"APPMETH{method_num}_DEPTHS"][depth] = getattr(
                        view, f"appmeth{method_num}_depth{depth}cm"
                    ).isChecked()

        else:
            # All application methods have distances
            config[f"APPMETH{method_num}_DISTANCES"] = {}
            if method_num == FOLIAR_APPMETHOD:
                config[f"APPMETH{method_num}_DRIFT_ONLY"] = {}

            for distance in ALL_DISTANCES:
                config[f"APPMETH{method_num}_DISTANCES"][distance] = getattr(
                    view, f"appmeth{method_num}_{distance}"
                ).isChecked()

                # Handle special case of method 2 having both standard and drift only options
                if method_num == FOLIAR_APPMETHOD:
                    config[f"APPMETH{method_num}_DRIFT_ONLY"][distance] = getattr(
                        view, f"appmeth{method_num}_{distance}_driftonly"
                    ).isChecked()


def _add_assessment_settings(config: dict[str, Any], view):
    """Adds the assessment settings to the config"""

    if view.fifraRadButton.isChecked():
        config["ASSESSMENT_TYPE"] = "fifra"
    else:
        config["ASSESSMENT_TYPE"] = "esa"
