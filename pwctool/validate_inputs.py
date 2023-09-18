"""Functions to validate tool input files"""


import os
from typing import Any
import re
import pandas as pd
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
        err_message = "The output directory does not exist. Please choose a valid directory and try again."
        _display_error_message(error_dialog, err_message)
        return False

    if not os.path.exists(config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"]):
        err_message = (
            "The Ag Practices Table does not exist or the path is incorrect. Please ensure it is valid and try again."
        )
        _display_error_message(error_dialog, err_message)
        return False

    if not os.path.exists(config["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"]):
        err_message = "The AgDRIFT Reduction table does not exist or the path is incorrect. Please ensure it is valid and try again."
        _display_error_message(error_dialog, err_message)
        return False

    if not os.path.exists(config["FILE_PATHS"]["SCENARIO_FILES_PATH"]):
        err_message = "The scenario files directory does not exist or the path is incorrect. Please ensure it is valid and try again."
        _display_error_message(error_dialog, err_message)
        return False

    if config["USE_CASE"] == "Use Case #1":
        if not os.path.exists(config["FILE_PATHS"]["INGR_FATE_PARAMS"]):
            err_message = "The ingr. fate parameters table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)
            return False

        if not os.path.exists(config["FILE_PATHS"]["WETTEST_MONTH_CSV"]):
            err_message = "The wettest month table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)
            return False

        if not os.path.exists(config["FILE_PATHS"]["BIN_TO_LANDSCAPE"]):
            err_message = "The bin to landscape lookup table does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)
            return False

    elif config["USE_CASE"] == "Use Case #2":
        if not os.path.exists(config["FILE_PATHS"]["PWC_BATCH_CSV"]):
            err_message = "The input pwc batch file does not exist or the path is incorrect. Please ensure it is valid and try again."
            _display_error_message(error_dialog, err_message)
            return False

    if config["RUN_ID"] == "":
        error_dialog.errMsgLabel.setText("Please create a run id and try again.")
        error_dialog.exec_()
        return False

    return True


def _validate_apt(config: dict[str, Any], error_dialog: QDialog):
    """Validates the ag practices table. Checks:
        - the APT is closed
        - the first column of the APT is "RunDescriptor"
        - the annual restrictions and PHI are entered
        - the annual maximum number of apps and PHI are integers
        - the annual maximum amount is an integer or float
        - the pre E and post E maxamt and maxnumapps are the correct type if entered
        - MaxAppRate is the correct type
        - MaxNumApps is the correct type
        - rate 1 has max app rate specified
        - MRI is specified but max app rate is not for any rate, notify user
        - rate pre E MRI is an integer if entered
        - rate post E MRI is an integer if entered
        - the rate instructions format is entered correctly

    If there is an issue with any of the checks, an error is raised and the execution is terminated.
    """

    # check that the APT file is closed (prevents permission error)
    try:
        ag_practices: pd.DataFrame = pd.read_excel(
            config["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"], sheet_name=config["APT_SCENARIO"]
        )
    except PermissionError:
        err_message = "You might have the Ag Practices Table open in Excel. Please close it before running."
        _display_error_message(error_dialog, err_message)
        return False
    except ValueError:  # this should only happen when permission error is handled (apt file is open when config is loaded) and user immediately executes
        if config["APT_SCENARIO"] == "":
            err_message = "Something is wrong with the specified Ag Practices Table sheet name. Please respecify the Ag Practices Table path and try again."
            _display_error_message(error_dialog, err_message)
        else:
            err_message = "An unknown error occured. Please save the configuration, reload it, and try executing again."
            _display_error_message(error_dialog, err_message)
        return False

    # check that the first column of the apt is RunDescriptor
    try:
        ag_practices.set_index(keys="RunDescriptor", inplace=True)
    except KeyError:
        err_message = "Ensure the first column of the Ag Practices Table is 'RunDescriptor' and try again."
        _display_error_message(error_dialog, err_message)
        return False

    # TODO: check that the drift profile values are correct

    for indx, row in ag_practices.iterrows():
        # check that the annual restrictions and PHI are entered
        if any(pd.isna(y) for y in [row["MaxAnnAmt_lbsacre"], row["MaxAnnNumApps"], row["PHI"]]):
            err_message = f"The MaxAnnAmt_lbsacre, MaxAnnNumApps, or PHI is not specified for {indx} in Ag Practices Table. Ensure these are entered correctly and try again."
            _display_error_message(error_dialog, err_message)
            return False

        # check that the annual maximum number of apps and PHI are integers
        if not all(isinstance(b, int) for b in [row["MaxAnnNumApps"], row["PHI"]]):
            err_message = (
                f"Ensure the MaxAnnNumApps and PHI for {indx} in Ag Practices Table are integers and try again."
            )
            _display_error_message(error_dialog, err_message)
            return False

        # check that the annual maximum amount is an integer or float
        if not isinstance(row["MaxAnnAmt_lbsacre"], (int, float)):
            err_message = f"Ensure the AnnMaxAmt for {indx} in Ag Practices Table is an integer or float and try again."
            _display_error_message(error_dialog, err_message)
            return False

        # check that the pre E and post E maxamt and maxnumapps are the correct type if entered
        for max_amt in ["PreEmergence_MaxAmt_lbsacre", "PostEmergence_MaxAmt_lbsacre"]:
            if pd.notna(row[max_amt]):
                if not isinstance(row[max_amt], (int, float)):
                    err_message = f"Ensure the PreEmergence_MaxAmt_lbsacre and PostEmergence_MaxAmt_lbsacre for {indx} in Ag Practices Table are an integer or float and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

        for max_num_apps in ["PreEmergence_MaxNumApps", "PostEmergence_MaxNumApps"]:
            if pd.notna(row[max_num_apps]):
                if not isinstance(row[max_num_apps], int):
                    max_num_apps_asint = int(row[max_num_apps])
                    if max_num_apps_asint != row[max_num_apps]:
                        err_message = f"Ensure the PreEmergence_MaxNumApps and PostEmergence_MaxNumApps for {indx} in Ag Practices Table are integers and try again."
                        _display_error_message(error_dialog, err_message)
                        return False

        # check rate info validity
        for i in [1, 2, 3, 4]:
            max_app_rate = row[f"Rate{i}_MaxAppRate_lbsacre"]
            max_num_apps = row[f"Rate{i}_MaxNumApps"]
            rate_instr = row[f"Rate{i}_Instructions"]
            pre_e_mri = row[f"Rate{i}_PreEmergenceMRI"]
            post_e_mri = row[f"Rate{i}_PostEmergenceMRI"]

            # check if either pre or post E MRI is specified for any rates that have info entered
            if any(pd.notna(j) for j in [max_app_rate, max_num_apps, rate_instr]):  # at least one is not nan
                if all(pd.isna(x) for x in [pre_e_mri, post_e_mri]):
                    err_message = f"Ensure either the PreEmergenceMRI or PostEmergenceMRI is specified for rate {i} for {indx} in Ag Practices Table. An integer value must be entered for either the Pre or Post MRI for a valid rate. See the reader's guide for more info."
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
                    err_message = f"Ensure there is a MaxAppRate specified for Rate 1 for {indx} in the Ag Practices Table. Rate 1 must have a valid MaxAppRate. Please ensure it does and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

            # if MRI is specified but max app rate is not for any rate
            if any(pd.notna(l) for l in [pre_e_mri, post_e_mri]):  # if any is not nan
                if pd.isna(max_app_rate):
                    err_message = f"Ensure there is a MaxAppRate specified for rate {i} for {indx} in the Ag Practices Table if there is a Pre or Post Emergence MRI specified. Please ensure a MaxAppRate is specified if an MRI is specified and try again."
                    _display_error_message(error_dialog, err_message)
                    return False

                # check that the rate pre E MRI is an integer if entered
                if pd.notna(pre_e_mri):
                    if not isinstance(pre_e_mri, int):
                        pre_e_mri_asint = int(pre_e_mri)
                        if pre_e_mri != pre_e_mri_asint:
                            err_message = f"Ensure that the PreEmergenceMRI for rate {i} for {indx} in the Ag Practices Table is an integer and try again."
                            _display_error_message(error_dialog, err_message)
                            return False

                # check that the rate post E MRI is an integer if entered
                if pd.notna(post_e_mri):
                    if not isinstance(post_e_mri, int):
                        post_e_mri_asint = int(post_e_mri)
                        if post_e_mri != post_e_mri_asint:
                            err_message = f"Ensure that the PostEmergenceMRI for rate {i} for {indx} in the Ag Practices Table is an integer and try again."
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
        err_message = "There is something wrong with the rate specific instructions in the Ag Practices Table. Please check that the formatting is valid as listed in the reader's guide and try again."
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
