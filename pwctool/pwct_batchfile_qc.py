"""
PWC batch file QC module

Manages QC of existing batch file
"""

import os
import sys
import linecache
import logging
import copy
from datetime import date, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py

APP_AMT_THRESHOLD = 0.002  # fudge factor to account for rounding


def standardize_field_names(input_pwc_batch_file: pd.DataFrame) -> pd.DataFrame:
    """Standardizes field names for input batch file before QC."""

    orig_column_names = input_pwc_batch_file.columns.tolist()
    new_column_names = copy.deepcopy(orig_column_names)

    standard_column_names = [
        "Run Descriptor",
        "Run Name",
        "SorptionCoefficient(mL/g)",
        "kocflag",
        "WaterColumnMetabolismHalflife(day)",
        "WaterReferenceTemperature(C) ",
        "BenthicMetabolismHalflife(day)",
        "BenthicReferenceTemperature(C) ",
        "AqueousPhotolysisHalflife(day)",
        "PhotolysisReferenceLatitude(?)",
        "HydrolysisHalflife(days)",
        "SoilHalflife(days)",
        "SoilReferencerTemperature(C) ",
        "FoliarHalflife(day)",
        "MolecularWeight(g/mol)",
        "VaporPressure(torr)",
        "Solubility(mg/L)",
        "Henry's Constant (unitless)",
        "Air Diffusion (cm3/d)",
        "Heat of Henry (J/mol)",
        "HUC2",
        "Scenario",
        "weather overide",
        "blank 1",
        "blank 2",
        "blank 3",
        "blank 4",
        "blank 5",
        "blank 6",
        "blank 7",
        "blank 8",
        "blank 9",
        "blank 10",
        "AquaticBin",
        "FlowAvgTime",
        "Field Size (m2)",
        "Waterbody Area (m2)",
        "Init Depth (m)",
        "Max Depth (m)",
        "HL (m)",
        "PUA",
        "Baseflow",
        "Num_Daysheds",
        "IRF1",
        "IRF2",
        "IRF3",
        "IRF4",
        "IRF5",
        "IRF6",
        "IRF7",
        "IRF8",
        "IRF9",
        "IRF10",
        "IRF11",
        "IRF12",
        "IRF13",
        "IRF14",
        "IRF15",
        "IRF16",
        "IRF17",
        "IRF18",
        "IRF19",
        "IRF20",
        "IRF21",
        "IRF22",
        "IRF23",
        "IRF24",
        "IRF25",
        "IRF26",
        "IRF27",
        "IRF28",
        "IRF29",
        "IRF30",
        "IRF31",
        "NumberofApplications",
        "Absolute Dates?",
        "Relative Dates?",
    ]

    for indx, _ in enumerate(standard_column_names):
        new_column_names[indx] = standard_column_names[indx]

    input_pwc_batch_file.rename(dict(zip(orig_column_names, new_column_names)), axis=1, inplace=True)

    return input_pwc_batch_file


def create_storage_table() -> dict[str, list]:
    """Creates a table to store results."""

    storage_table: dict[str, list] = {
        # data from source
        "RunDescriptor": [],
        "RunName": [],
        "HUC": [],
        "Bin": [],
        "Scenario": [],
        "EmergenceDate": [],
        "HarvestDate": [],
        "AppRates(kg/ha)": [],
        "AppDates (sorted)": [],
        # derived and check
        "Check_Ann_NumApps_NotExceeded": [],
        "Modeled_Ann_NumApps": [],
        "Label_Ann_NumApps": [],
        #
        "Check_Ann_Amt_NotExceeded": [],
        "Modeled_Ann_Amt": [],
        "Label_Ann_Amt": [],
        "Difference_Ann_Amt": [],
        #
        "Check_PreE_NumApps_NotExceeded": [],
        "Modeled_PreE_NumApps": [],
        "Label_PreE_NumApps": [],
        #
        "Check_PreE_Amt_NotExceeded": [],
        "Modeled_PreE_Amt": [],
        "Label_PreE_Amt": [],
        "Difference_PreE_Amt": [],
        #
        "Check_PostE_NumApps_NotExceeded": [],
        "Modeled_PostE_NumApps": [],
        "Label_PostE_NumApps": [],
        #
        "Check_PostE_Amt_NotExceeded": [],
        "Modeled_PostE_Amt": [],
        "Label_PostE_Amt": [],
        "Difference_PostE_Amt": [],
        #
        "Check_MRI_NotWithin": [],  # assume label mris are equal for both intervals accross all rates
        "Modeled_MRIs": [],
        "Label_MRI": [],
        #
        # "Check_Drifts_AreCorrect": [],
        # "Modeled_Drifts": [],
        # "Label_Drift": [],
        # #
        # "Check_Effs_AreCorrect": [],
        # "Modeled_Effs": [],
        # "Label_Eff": [],
        #
        "Check_NoDuplicate_AppDates": [],
        "Check_PreHarvInt_NotWithin": [],
        "Label_PreHarvInt": [],
        #
        "Check_NumAppsField_IsCorrect": [],  # check that number of listed apps field is correct
        "NumAppsField": [],
        "Modeled_NumApps": [],
    }

    return storage_table


def get_emergence_harvest_dates(scenario: str, scenario_files_dir: str) -> tuple[date, date]:
    """Gets the emergence and harvest date from the scenario files based on the scenario."""

    scenario_file = os.path.join(scenario_files_dir, scenario)
    # extract date information from specific lines in .scn files
    emergence_day = int(linecache.getline(scenario_file, 28))
    emergence_month = int(linecache.getline(scenario_file, 29))
    harvest_day = int(linecache.getline(scenario_file, 32))
    harvest_month = int(linecache.getline(scenario_file, 33))
    # use arbitrary year that is not a leap year to complete the date
    emergence_date = date(year=2021, month=emergence_month, day=emergence_day)
    harvest_date = date(year=2021, month=harvest_month, day=harvest_day)

    return emergence_date, harvest_date


def prepare_apt(apt: pd.DataFrame) -> pd.DataFrame:
    """Prepares the APT for QC.
    1. Converts lb/acre to kg/ha for rate columns
    2. Assigns value to interval restrictions

    Args:
        apt (pd.DataFrame): ag practices table

    Returns:
        pd.DataFrame: ag practices table
    """

    # convert amt field units to kg/ha to match batch file
    apt["MaxAnnAmt"] = apt["MaxAnnAmt"] * 1.120851  # convert from lbs/ac to kg/ha
    apt["PostEmergence_MaxAmt"] = apt["PostEmergence_MaxAmt"] * 1.120851
    apt["PreEmergence_MaxAmt"] = apt["PreEmergence_MaxAmt"] * 1.120851

    # apt.replace(to_replace=np.nan, value=pd.NA, inplace=True)
    apt = apt.reset_index(drop=False)
    # set interval max amt and max num apps based on specific rates
    def set_up_interval_fields(interval: str):
        """Updates interval restrictions fields based
        on interval validity. Specifies interval max
        num apps and max amt numerically."""
        # get all rows where interval_MaxAmt is NA and
        # one or more rate specific interval MRIs is not NA
        # for these rows, interval is a valid interval but
        # the amount is unspecified, so write it as max ann amt
        apt.loc[
            pd.isna(apt[f"{interval}_MaxAmt"])
            & (
                (pd.notna(apt[f"Rate1_{interval}MRI"]))
                | (pd.notna(apt[f"Rate2_{interval}MRI"]))
                | (pd.notna(apt[f"Rate3_{interval}MRI"]))
                | (pd.notna(apt[f"Rate4_{interval}MRI"]))
            ),
            f"{interval}_MaxAmt",
        ] = apt["MaxAnnAmt"]

        # get all rows where interval_MaxAmt is NA and
        # all of the rate specific interval MRIs are NA
        # for these rows, interval is not a valid interval
        # so write the amount as zero
        apt.loc[
            pd.isna(apt[f"{interval}_MaxAmt"])
            & (pd.isna(apt[f"Rate1_{interval}MRI"]))
            & (pd.isna(apt[f"Rate2_{interval}MRI"]))
            & (pd.isna(apt[f"Rate3_{interval}MRI"]))
            & (pd.isna(apt[f"Rate4_{interval}MRI"])),
            f"{interval}_MaxAmt",
        ] = 0

        # same thing for number of apps
        apt.loc[
            pd.isna(apt[f"{interval}_MaxNumApps"])
            & (
                (pd.notna(apt[f"Rate1_{interval}MRI"]))
                | (pd.notna(apt[f"Rate2_{interval}MRI"]))
                | (pd.notna(apt[f"Rate3_{interval}MRI"]))
                | (pd.notna(apt[f"Rate4_{interval}MRI"]))
            ),
            f"{interval}_MaxNumApps",
        ] = apt["MaxAnnNumApps"]

        apt.loc[
            pd.isna(apt[f"{interval}_MaxNumApps"])
            & (pd.isna(apt[f"Rate1_{interval}MRI"]))
            & (pd.isna(apt[f"Rate2_{interval}MRI"]))
            & (pd.isna(apt[f"Rate3_{interval}MRI"]))
            & (pd.isna(apt[f"Rate4_{interval}MRI"])),
            f"{interval}_MaxNumApps",
        ] = 0

    set_up_interval_fields("PreEmergence")
    set_up_interval_fields("PostEmergence")

    apt.set_index(keys="RunDescriptor", inplace=True, drop=True)
    return apt


def qc_batch_file(
    pwc_batch_file: pd.DataFrame, apt: pd.DataFrame, drt: pd.DataFrame, settings: dict[str, Any]
) -> dict[str, list]:
    """Quality checks each run in an input batch file.
    Performs the following checks:
    1. Annual maximum number of apps not exceeded
    2. Annual maximum amount not exceeded
    3. Pre-Emergence maximum number of apps not exceeded
    4. Pre-Emergence maximum amount not exceeded
    5. Post-Emergence maximum number of apps not exceeded
    6. Post-Emergence maximum amount not exceeded
    7. MRI is adhered to
    8. Drift values are correct
    9. Eff values are correct
    10. No duplicate app dates
    11. PHI not encroached
    12. Number of apps field is correct

    Currently does not check that rate specific instructions
    are satisfied.

    Args:
        pwc_batch_file (pd.DataFrame): input pwc batch file
        apt (pd.DataFrame): ag practices table
        drt (pd.DataFrame): drift reduction table

    Returns:
        dict[str, list]: qc results
    """
    # TODO: build in checks for specific rate instructions
    apt = prepare_apt(apt)
    storage_table: dict[str, list] = create_storage_table()

    for _, run in pwc_batch_file.iterrows():
        run.dropna(inplace=True)
        try:
            run_ag_practices: pd.Series = apt.loc[run["Run Descriptor"]].copy(deep=True).squeeze()
        except KeyError:
            logger.warning(f"\n WARNING: Run descriptor {run['Run Descriptor']} is not in APT. Skipped.")
            continue

        storage_table["RunDescriptor"].append(run["Run Descriptor"])
        storage_table["RunName"].append(run["Run Name"])

        #### gather source information ####
        app_rates = tuple(run[run.index.str.contains("AppRate")])
        storage_table["AppRates(kg/ha)"].append(app_rates)

        app_days = list(run[run.index.str.startswith("Day")])
        app_months = list(run[run.index.str.contains("Month")])
        app_dates = [
            date(year=2021, month=int(app_month), day=int(app_day)) for app_day, app_month in zip(app_days, app_months)
        ]
        app_dates.sort()
        storage_table["AppDates (sorted)"].append([app_date.strftime("%m/%d/%Y") for app_date in app_dates])

        storage_table["HUC"].append(run["HUC2"])
        storage_table["Bin"].append(run["AquaticBin"])
        storage_table["Scenario"].append(run["Scenario"])

        ##### derive and check ####
        emergence_date, harvest_date = get_emergence_harvest_dates(
            run["Scenario"], settings["FILE_PATHS"]["SCENARIO_FILES_PATH"]
        )
        storage_table["EmergenceDate"].append(emergence_date.strftime("%m/%d/%Y"))
        storage_table["HarvestDate"].append(harvest_date.strftime("%m/%d/%Y"))

        num_apps_pre = 0
        num_apps_post = 0
        sum_app_rates_pre = 0
        sum_app_rates_post = 0
        for app_date, app_rate in zip(app_dates, app_rates):

            if emergence_date < harvest_date:  # harvest date is after emergence date, annuals
                if emergence_date <= app_date <= harvest_date:  # post-emergence
                    sum_app_rates_post += app_rate
                    num_apps_post += 1
                else:  # pre-emergence
                    num_apps_pre += 1
                    sum_app_rates_pre += app_rate
            else:  # harvest date is after emergence date, overwinter
                if harvest_date < app_date < emergence_date:  # pre-emergence
                    sum_app_rates_pre += app_rate
                    num_apps_pre += 1
                else:  # post-emergence
                    num_apps_post += 1
                    sum_app_rates_post += app_rate

        # maximum annual number of apps
        if len(app_dates) <= run_ag_practices["MaxAnnNumApps"]:
            storage_table["Check_Ann_NumApps_NotExceeded"].append(True)
        else:
            storage_table["Check_Ann_NumApps_NotExceeded"].append(False)
        storage_table["Modeled_Ann_NumApps"].append(len(app_dates))
        storage_table["Label_Ann_NumApps"].append(run_ag_practices["MaxAnnNumApps"])

        # maximum annual amount
        if sum(app_rates) <= (run_ag_practices["MaxAnnAmt"] + APP_AMT_THRESHOLD):
            storage_table["Check_Ann_Amt_NotExceeded"].append(True)
        else:
            storage_table["Check_Ann_Amt_NotExceeded"].append(False)
        storage_table["Modeled_Ann_Amt"].append(sum(app_rates))
        storage_table["Label_Ann_Amt"].append(run_ag_practices["MaxAnnAmt"])
        storage_table["Difference_Ann_Amt"].append(sum(app_rates) - run_ag_practices["MaxAnnAmt"])

        # pre-emergence num apps
        if num_apps_pre <= run_ag_practices["PreEmergence_MaxNumApps"]:
            storage_table["Check_PreE_NumApps_NotExceeded"].append(True)
        else:
            storage_table["Check_PreE_NumApps_NotExceeded"].append(False)
        storage_table["Modeled_PreE_NumApps"].append(num_apps_pre)
        storage_table["Label_PreE_NumApps"].append(run_ag_practices["PreEmergence_MaxNumApps"])

        # pre-emergence max amt
        if sum_app_rates_pre <= (run_ag_practices["PreEmergence_MaxAmt"] + APP_AMT_THRESHOLD):
            storage_table["Check_PreE_Amt_NotExceeded"].append(True)
        else:
            storage_table["Check_PreE_Amt_NotExceeded"].append(False)
        storage_table["Modeled_PreE_Amt"].append(sum_app_rates_pre)
        storage_table["Label_PreE_Amt"].append(run_ag_practices["PreEmergence_MaxAmt"])
        storage_table["Difference_PreE_Amt"].append(sum_app_rates_pre - run_ag_practices["PreEmergence_MaxAmt"])

        # post-emergence num apps
        if num_apps_post <= run_ag_practices["PostEmergence_MaxNumApps"]:
            storage_table["Check_PostE_NumApps_NotExceeded"].append(True)
        else:
            storage_table["Check_PostE_NumApps_NotExceeded"].append(False)
        storage_table["Modeled_PostE_NumApps"].append(num_apps_post)
        storage_table["Label_PostE_NumApps"].append(run_ag_practices["PostEmergence_MaxNumApps"])

        # post-emergece max amt
        if sum_app_rates_post <= (run_ag_practices["PostEmergence_MaxAmt"] + APP_AMT_THRESHOLD):
            storage_table["Check_PostE_Amt_NotExceeded"].append(True)
        else:
            storage_table["Check_PostE_Amt_NotExceeded"].append(False)
        storage_table["Modeled_PostE_Amt"].append(sum_app_rates_post)
        storage_table["Label_PostE_Amt"].append(run_ag_practices["PostEmergence_MaxAmt"])
        storage_table["Difference_PostE_Amt"].append(sum_app_rates_post - run_ag_practices["PostEmergence_MaxAmt"])

        # check MRIs
        modeled_mris = []
        for i, _ in enumerate(app_dates[:-1]):
            modeled_mris.append((app_dates[i + 1] - app_dates[i]).days)
        storage_table["Modeled_MRIs"].append(modeled_mris)

        if pd.notna(run_ag_practices["Rate1_PreEmergenceMRI"]):
            label_mri = run_ag_practices["Rate1_PreEmergenceMRI"]
        else:
            label_mri = run_ag_practices["Rate1_PostEmergenceMRI"]
        storage_table["Label_MRI"].append(label_mri)

        if all([mri >= label_mri for mri in modeled_mris]):
            storage_table["Check_MRI_NotWithin"].append(True)
        else:
            storage_table["Check_MRI_NotWithin"].append(False)

        # check drift
        # drifts = tuple(run[run.index.str.contains("Drift")])
        # drift_profile = f"{run['AquaticBin']}-{run_ag_practices['DriftProfile']}"
        # # TODO: build in ability to check different distances
        # # not sure we can check this accurately
        # # would need to parse the distance from the "Run Name" field
        # # would require consistent naming convention for all runs
        # # would not work with batch built without the ADT
        # drift_factor = drt.at[drift_profile, "000m"]

        # if all(drift == drift_factor for drift in drifts):
        #     storage_table["Check_Drifts_AreCorrect"].append(True)
        # else:
        #     storage_table["Check_Drifts_AreCorrect"].append(False)
        # storage_table["Label_Drift"].append(drift_factor)
        # storage_table["Modeled_Drifts"].append(drifts)

        # # check effs
        # effs = tuple(run[run.index.str.contains("Eff")])
        # eff_factor = drt.at[drift_profile, "Efficiency"]
        # if all(eff == eff_factor for eff in effs):
        #     storage_table["Check_Effs_AreCorrect"].append(True)
        # else:
        #     storage_table["Check_Effs_AreCorrect"].append(False)
        # storage_table["Modeled_Effs"].append(effs)
        # storage_table["Label_Eff"].append(eff_factor)

        # check for duplicate dates
        duplicate_dates = [app_date for app_date in app_dates if app_dates.count(app_date) > 1]
        if len(duplicate_dates) > 0:
            storage_table["Check_NoDuplicate_AppDates"].append(False)
        else:
            storage_table["Check_NoDuplicate_AppDates"].append(True)

        # pre-harvest interval
        pre_harv_int_end = harvest_date
        pre_harv_int_start = pre_harv_int_end - timedelta(days=int(run_ag_practices["PHI"]))

        if pre_harv_int_start.year == 2020:  # perennial, need to account for
            print("preharvest interval goes into previous year, need to account for this")
            sys.exit()

        phi_not_encroached = True
        for app_date in app_dates:
            if pre_harv_int_start < app_date <= pre_harv_int_end:  # app date is within PHI
                phi_not_encroached = False
                break
            phi_not_encroached = True
        storage_table["Check_PreHarvInt_NotWithin"].append(phi_not_encroached)
        storage_table["Label_PreHarvInt"].append(run_ag_practices["PHI"])

        # check that the number of applications field is correct
        if len(app_dates) == run["NumberofApplications"]:
            storage_table["Check_NumAppsField_IsCorrect"].append(True)
        else:
            storage_table["Check_NumAppsField_IsCorrect"].append(False)
        storage_table["NumAppsField"].append(run["NumberofApplications"])
        storage_table["Modeled_NumApps"].append(len(app_dates))

    return storage_table
