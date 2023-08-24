"""Functions to validate tool input files"""


import os
from typing import Any
import re
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QDialog


def _display_error_message(error_dialog: QDialog, message: str):
    """Displays an error message"""
    error_dialog.errMsgLabel.setText(message)
    error_dialog.exec_()


def validate_input_files(config: dict[str, Any], error_dialog: QDialog):
    """Validates the input files prior to tool execution. Notifies user
    if something is incorrect and prevents execution."""

    if (
        _validate_config(config, error_dialog)
        and _validate_apt(config, error_dialog)
        and _validate_drt(config, error_dialog)
    ):
        return True
    else:
        return False


def _validate_config(config: dict[str, Any], error_dialog: QDialog) -> bool:
    """Checks that each input file/folder in the config exists"""

    if not os.path.exists(config["FILE_PATHS"]["OUTPUT_DIR"]):
        err_message = "Output directory does not exist. Please choose a valid directory and try again."
        _display_error_message(error_dialog, err_message)

    if not os.path.exists(config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"]):
        err_message = "The agronomic practices table does not exist or the path is incorrect. Please ensure it is valid and try again."
        _display_error_message(error_dialog, err_message)

    if not os.path.exists(config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"]):
        err_message = "The AgDRIFT Reduction table does not exist or the path is incorrect. Please ensure it is valid and try again."
        _display_error_message(error_dialog, err_message)

    if not os.path.exists(config["FILE_PATHS"]["SCENARIO_FILES_PATH"]):
        err_message = "The scenario files directory does not exist or the path is incorrect. Please ensure it is valid and try again."
        _display_error_message(error_dialog, err_message)

    if config["USE_CASE"] == "Use Case #1":
        if not os.path.exists(config["FILE_PATHS"]["INGR_FATE_PARAMS"]):
            err_message = "The ingr. fate parameters table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)

        if not os.path.exists(config["FILE_PATHS"]["WETTEST_MONTH_CSV"]):
            err_message = "The wettest month table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)

        if not os.path.exists(config["FILE_PATHS"]["BIN_TO_LANDSCAPE"]):
            err_message = "The bin to landscape lookup table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)

    elif config["USE_CASE"] == "Use Case #2":
        if not os.path.exists(config["FILE_PATHS"]["PWC_BATCH_CSV"]):
            err_message = "The input pwc batch file does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)

    if config["RUN_ID"] == "":
        error_dialog.errMsgLabel.setText("Please create a run id and try again.")
        error_dialog.exec_()
        return False

    return True


def _validate_apt(config: dict[str, Any], error_dialog: QDialog):
    """Validates the ag practices table. Checks:
        - the first column of the APT is "RunDescriptor"
        - check that the annual restrictions are entered
        - check that the types are correct
        - check that a value is entered for either pre or post E MRI for all rates
        - rate 1 has valid max app rate specified
        - if MRI is specified but lacks other rate info, notify user
        - the rate instructions format is entered correctly

    If there is an issue with any of the checks, an error is raised and the execution is terminated.
    """

    # check that the first column of the apt is RunDescriptor
    ag_practices_excel_obj = pd.ExcelFile(config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"], engine="openpyxl")
    ag_practices: pd.DataFrame = pd.read_excel(ag_practices_excel_obj, sheet_name=config["APT_SCENARIO"])

    try:
        ag_practices.set_index(keys="RunDescriptor", inplace=True)
    except KeyError:
        err_message = "Please ensure the first column of the APT is 'RunDescriptor' and try again."
        _display_error_message(error_dialog, err_message)

    for indx, row in ag_practices.iterrows():
        # check that the annual restrictions and PHI are entered
        if any(pd.isna(y) for y in [row["MaxAnnAmt"], row["MaxAnnNumApps"], row["PHI"]]):
            err_message = f"It looks like the annual restrictions or PHI are not specified for {indx} in Ag Practices Table. Please ensure these are entered correctly and try again."
            _display_error_message(error_dialog, err_message)
            return False

        # check that the annual maximum number of apps and PHI are integers
        if not all(isinstance(b, int) for b in [row["MaxAnnNumApps"], row["PHI"]]):
            err_message = f"Please ensure annual MaxAnnNumApps and PHI for {indx} in Ag Practices Table are integers and try again."
            _display_error_message(error_dialog, err_message)
            return False

        # check that the annual maximum amount is an integer or float
        if not isinstance(row["MaxAnnAmt"], (int, float)):
            err_message = (
                f"Please ensure the AnnMaxAmt for {indx} in Ag Practices Table is an integer or float and try again."
            )
            _display_error_message(error_dialog, err_message)
            return False

        # check that the pre E and post E maxamt and maxnumapps are the correct type if entered
        for max_amt in ["PreEmergence_MaxAmt", "PostEmergence_MaxAmt"]:
            if pd.notna(row[max_amt]):
                if not isinstance(row[max_amt], (int, float)):
                    err_message = f"Please ensure the PreEmergence_MaxAmt and PostEmergence_MaxAmt for {indx} in Ag Practices Table are an integer or float and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

        for max_num_apps in ["PreEmergence_MaxNumApps", "PostEmergence_MaxNumApps"]:
            if pd.notna(row[max_num_apps]):
                if not isinstance(row[max_num_apps], int):
                    max_num_apps_asint = int(row[max_num_apps])
                    if max_num_apps_asint != row[max_num_apps]:
                        err_message = f"Please ensure the PreEmergence_MaxNumApps and PostEmergence_MaxNumApps for {indx} in Ag Practices Table are integers and try again."
                        _display_error_message(error_dialog, err_message)
                        return False

        # check rate info validity
        for i in [1, 2, 3, 4]:
            max_app_rate = row[f"Rate{i}_MaxAppRate"]
            max_num_apps = row[f"Rate{i}_MaxNumApps"]
            rate_instr = row[f"Rate{i}_Instructions"]
            pre_e_mri = row[f"Rate{i}_PreEmergenceMRI"]
            post_e_mri = row[f"Rate{i}_PostEmergenceMRI"]

            # check if either pre or post E MRI is specified for any rates that have info entered
            if any(pd.notna(j) for j in [max_app_rate, max_num_apps, rate_instr]):  # at least one is not nan
                if all(pd.isna(x) for x in [pre_e_mri, post_e_mri]):
                    err_message = f"Either the Pre Emergence or Post Emergence MRI is not be specified for rate {i} for {indx} in Ag Practices Table. Either the Pre E or Post E MRI must be specified for any valid rate. Please see the reader's guide for more information."
                    _display_error_message(error_dialog, err_message)
                    return False

                # check that MaxAppRate is the correct type
                if pd.notna(max_app_rate):
                    if not isinstance(max_app_rate, (int, float)):
                        err_message = f"Ensure that the MaxAppRate for rate {i} for {indx} in the Ag Practices Table is an integer or float and try again."
                        _display_error_message(error_dialog, err_message)
                        return False

                # check that MaxNumApps is the correct type
                if pd.notna(max_num_apps):
                    if not isinstance(max_num_apps, int):
                        max_num_apps_asint = int(max_num_apps)
                        if max_num_apps != max_num_apps_asint:
                            err_message = f"Ensure that the MaxNumApps for rate {i} for {indx} in the Ag Practices Table is an integer and try again."
                            _display_error_message(error_dialog, err_message)
                            return False

            # make sure rate 1 has max app rate specified
            if i == 1:
                if pd.isna(max_app_rate):
                    err_message = f"It looks like there is no max app rate specified for Rate 1 for {indx} in the Ag Practices Table. Rate 1 must have a valid application rate. Please ensure it does and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

            # if MRI is specified but max app rate is not for any rate, notify user
            if any(pd.notna(l) for l in [pre_e_mri, post_e_mri]):  # if any is not nan
                if pd.isna(max_app_rate):
                    err_message = f"It looks like there is no max app rate specified for rate {i} for {indx} in the Ag Practices Table but there is an MRI specified for this rate. Please ensure a max rate is specified if an MRI is specified and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

                # check that the rate pre E MRI is an integer if entered
                if pd.notna(pre_e_mri):
                    if not isinstance(pre_e_mri, int):
                        pre_e_mri_asint = int(pre_e_mri)
                        if pre_e_mri != pre_e_mri_asint:
                            err_message = f"Ensure that the pre E MRI for rate {i} for {indx} in the Ag Practices Table is an integer and try again."
                            _display_error_message(error_dialog, err_message)
                            return False

                # check that the rate post E MRI is an integer if entered
                if pd.notna(post_e_mri):
                    if not isinstance(post_e_mri, int):
                        post_e_mri_asint = int(post_e_mri)
                        if post_e_mri != post_e_mri_asint:
                            err_message = f"Ensure that the post E MRI for rate {i} for {indx} in the Ag Practices Table is an integer and try again."
                            _display_error_message(error_dialog, err_message)
                            return False

    # check the rate instructions format
    rate_instructions: list = list(
        ag_practices.loc[:, ag_practices.columns.str.contains("Instructions")].to_numpy().flatten()
    )

    pattern1 = "[YN]_[HE][+-][0-9]+"  # for example: Y_H-30, N_E+30
    pattern2 = "[YN]_[HE0-9+-]+>[HE0-9+-]+"  # for example: N_0501>0615

    results = []
    for rate_instruction in rate_instructions:
        # check if rate instructions conform to general formatting
        if pd.isna(rate_instruction) or re.search(pattern1, rate_instruction) or re.search(pattern2, rate_instruction):
            results.append(True)
        else:
            results.append(False)

    if not all(result is True for result in results):
        err_message = "It looks like there something wrong with the rate specific instructions in the Ag Practices Table. Please check that the formatting is valid as listed in the reader's guide and try again."
        _display_error_message(error_dialog, err_message)
        return False

    return True


def _validate_drt(config: dict[str, Any], error_dialog: QDialog):
    """Validates the drift reduction table. Checks:
        - if the first column name is "Profile"
    If there is an issue, the execution is terminated.
    """

    # check the drt first column name
    drift_reduction_table: pd.DataFrame = pd.read_excel(
        config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"],
        sheet_name=config["DRT_SCENARIO"],
    )
    try:
        drift_reduction_table.set_index(keys="Profile", inplace=True)
    except KeyError:
        err_message = "Please ensure the first column of the DRT is 'Profile' and try again."
        _display_error_message(error_dialog, err_message)
        return False

    return True