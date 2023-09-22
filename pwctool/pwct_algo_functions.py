"""
Application assignment algorithm functions module

Extra function storage
"""


import logging
import operator
import calendar
from datetime import date, timedelta
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py

from pwctool.constants import BURIED_APPMETHODS


def lookup_states_from_crop(
    crop_to_state_lookup_table: pd.DataFrame, run_ag_practices: pd.Series, label_convention_states: dict[str, str]
) -> list:

    run_apt_states: str = run_ag_practices["States"].replace(" ", "")

    # get a list of the states permitted by label
    if run_apt_states == "All":
        label_states = label_convention_states["ALL"].split(",")
    elif run_apt_states == "EastofRockies":
        label_states = label_convention_states["EastofRockies"].split(",")
    elif run_apt_states == "WestofRockies":
        label_states = label_convention_states["WestofRockies"].split(",")
    elif "All" in run_apt_states:
        states_to_remove = run_apt_states.rsplit("-")[-1].split(",")
        all_states = label_convention_states["ALL"].split(",")
        label_states = [i for i in all_states if i not in states_to_remove]
    else:
        label_states = run_apt_states.split(",")

    # subset to get only states where crop is grown
    try:
        grown_states = crop_to_state_lookup_table.at[run_ag_practices["LabeledUse"], "States"].split(",")
    except KeyError:
        grown_states = label_convention_states["ALL"].split(",")

    # yield only states on label and grown
    model_states = [i for i in label_states if i in grown_states]

    return model_states


def lookup_huc_from_state(state_to_huc_lookup_table: pd.DataFrame, states: list[str]) -> list:
    """Gets the hucs that correspond to states in an APT row.

    Args:
        state_to_huc_lookup_table (pd.DataFrame): state to huc lookup table
        states (list): list of states to model

    Returns:
        list: hucs that correspond to states
    """

    model_hucs: list = []
    for state in states:
        try:
            model_hucs.append(state_to_huc_lookup_table.at[state, "HUC2s"].split(","))
        except KeyError:
            # state does not have any hucs associated with it
            # occurs for AK and HI for "new" hucs
            pass

    model_hucs: list = [item for sublist in model_hucs for item in sublist]
    model_hucs = set(model_hucs)
    model_hucs = sorted(model_hucs)

    return model_hucs


def get_drift_profile(run_ag_practices: pd.Series) -> str:
    """Gets the drift profile associate with the use (row in APT) app method.
    If the use is specified as an incorporated method (3-7), make sure the
    drift profile is NODRIFT
    """

    if run_ag_practices["ApplicationMethod"] in BURIED_APPMETHODS:
        drift_profile = "NODRIFT"
    else:
        drift_profile = run_ag_practices["DriftProfile"]

    return drift_profile


def get_interval(app_date: date, ag_practices: pd.Series) -> str:
    """Determines the interval for an application date. Post emergence interval is
    inclusive. Meaning if the app_date falls on the emergence or harvest date, it
    is considered post emergence.

    Args:
        app_date (date): Potential application date
        ag_practices (pd.Series): Ag practices information for the run

    Returns:
        str: The application interval of the application date
    """
    if ag_practices["Harvest"] > ag_practices["Emergence"]:  # harvest after emergence
        if ag_practices["Emergence"] <= app_date <= ag_practices["Harvest"]:
            current_interval = "PostEmergence"
        else:
            current_interval = "PreEmergence"
    else:  # harvest before emergence
        if ag_practices["Harvest"] < app_date < ag_practices["Emergence"]:
            current_interval = "PreEmergence"
        else:
            current_interval = "PostEmergence"

    return current_interval


def get_rate(
    ag_practices: pd.Series, count: pd.DataFrame, appdate_interval: str, settings: dict[str, Any], app_date: date
) -> tuple[str, float, bool]:
    """Gets the appropriate application rate and rate identifier as specified in
    the ag practices table. Iterates through the application rates from highest
    to lowest, and selects the first one that has not reached the max number of apps.
    Behavior is different depending on date prioritization (max app rate or wettest month).

    Args:
        ag_practices (pd.Series): Ag practices information
        count (pd.DataFrame): app tracking information
        settings (Dict[str,Any]): configuration

    Returns:
        tuple[str, float, bool]: rate identifier, app rate value, app rate validity
    """

    if settings["DATE_PRIORITIZATION"] == "Max App. Rate":

        for i in range(1, 5):

            if ag_practices[f"Rate{i}_MaxAppRate_lbsacre"] == np.inf:  # rate doesn't exist
                rate_id = pd.NA  # all valid rates have been accounted for
                app_rate = 0
                valid_app_rate = False

            else:
                # if the rate MaxNumApps have not been reached
                if count.at[f"Rate{i}", "num_apps"] < ag_practices[f"Rate{i}_MaxNumApps"]:

                    # check if the rate is only valid for an exhausted interval
                    if len(ag_practices[f"Rate{i}_ValidIntervals"]) == 1:

                        rate_interval = ag_practices[f"Rate{i}_ValidIntervals"][0]

                        # if the interval limits are not reached
                        if (count.at[rate_interval, "num_apps"] < ag_practices[f"{rate_interval}_MaxNumApps"]) and (
                            count.at[rate_interval, "amt_applied"] < ag_practices[f"{rate_interval}_MaxAmt_lbsacre"]
                        ):
                            rate_id = f"Rate{i}"
                            app_rate = ag_practices[f"Rate{i}_MaxAppRate_lbsacre"]
                            valid_app_rate = True
                            break

                    elif len(ag_practices[f"Rate{i}_ValidIntervals"]) == 2:
                        rate_id = f"Rate{i}"
                        app_rate = ag_practices[f"Rate{i}_MaxAppRate_lbsacre"]
                        valid_app_rate = True
                        break

                # all rates valid and accounted for, done applying
                rate_id = pd.NA
                app_rate = 0
                valid_app_rate = False

    else:  # date prioritization is wettest month
        for i in range(1, 5):

            if ag_practices[f"Rate{i}_MaxAppRate_lbsacre"] == np.inf:  # rate doesn't exist
                rate_id = pd.NA  # all valid rates have been accounted for
                app_rate = 0
                valid_app_rate = False

            else:  # rate exists

                # if the rate is not exausted
                if count.at[f"Rate{i}", "num_apps"] < ag_practices[f"Rate{i}_MaxNumApps"]:

                    # if current app date interval is in a valid rate interval
                    if appdate_interval in ag_practices[f"Rate{i}_ValidIntervals"]:

                        # if the current app date meets the rate instructions constraints
                        if meets_instruction_constraints(app_date, ag_practices, f"Rate{i}"):

                            rate_id = f"Rate{i}"
                            app_rate = ag_practices[f"Rate{i}_MaxAppRate_lbsacre"]
                            valid_app_rate = True
                            break

                # all rates valid and accounted for, done applying
                rate_id = pd.NA
                app_rate = 0
                valid_app_rate = False

    return rate_id, app_rate, valid_app_rate


def check_app_validity(
    app_date: date,
    appdate_interval: str,
    ag_practices: pd.Series,
    rate_id: str,
    applications: list,
    count: pd.DataFrame,
) -> bool:
    """Checks if the proposed application date is valid.

    Args:
        app_date (date): proposed application date
        appdate_interval (str): proposed application interval
        ag_practices (pd.Series): ag practices information
        rate_id (str): current application rate identifier
        applications (list): application date recordings
        count (pd.DataFrame): application recording

    Returns:
        bool: True if the proposed application is valid
    """

    if pd.isna(rate_id):
        return False
    else:
        return bool(
            (appdate_interval in ag_practices[f"{rate_id}_ValidIntervals"])
            and (count.at[appdate_interval, "num_apps"] + 1 <= ag_practices[f"{appdate_interval}_MaxNumApps"])
            and (
                count.at[appdate_interval, "amt_applied"] + 0.001 <= ag_practices[f"{appdate_interval}_MaxAmt_lbsacre"]
            )
            and (meets_instruction_constraints(app_date, ag_practices, rate_id))
            and (not within_mri(app_date, applications, int(ag_practices[f"{rate_id}_{appdate_interval}MRI"])))
            and (not within_phi(app_date, appdate_interval, ag_practices))
        )


def prepare_next_app(
    current_app_date: date,
    current_appdate_interval: str,
    current_rate_id: str,
    start_date: date,
    reverse_assigning: bool,
    ag_practices: pd.Series,
    applications: list,
    count: pd.DataFrame,
    settings: dict[str, Any],
) -> tuple[date, str, bool, bool, str, int, bool]:
    """Prepares the next application date. Checks if the next app should be forward or reverse
    assigned. Checks if the next application date is valid.

    Args:
        current_app_date (date): current (previous) application date
        current_appdate_interval (str): current (previous) application date interval
        next_rate_id (str): next application rate idenfitier
        start_date (date): the first application date in this series (while loop)
        reverse_assigning (bool): flag to discern reverse assigning
        ag_practices (pd.Series): ag practices information
        applications (list): previously recorded applications
        count (pd.DataFrame): application recording

    Returns:
        tuple[date, str, bool, bool]: next application date info
    """

    def get_next_reverse_date(current_app_date: date, mri: timedelta, ag_practices: pd.Series, applications: list):
        """Gets the next app date if reverse applying"""

        next_reverse_date = current_app_date - mri
        if next_reverse_date.year < current_app_date.year:
            next_reverse_date = date(year=2021, month=next_reverse_date.month, day=next_reverse_date.day)
        next_reverse_interval = get_interval(next_reverse_date, ag_practices)

        next_reverse_rate_id, next_reverse_app_rate, valid_next_app_rate = get_rate(
            ag_practices, count, next_reverse_interval, settings, next_reverse_date
        )

        if valid_next_app_rate:
            valid_next_date = check_app_validity(
                next_reverse_date,
                next_reverse_interval,
                ag_practices,
                next_reverse_rate_id,
                applications,
                count,
            )
        else:
            valid_next_date = False

        return (
            next_reverse_date,
            next_reverse_interval,
            valid_next_date,
            valid_next_app_rate,
            next_reverse_rate_id,
            next_reverse_app_rate,
        )

    mri = timedelta(days=int(ag_practices[f"{current_rate_id}_{current_appdate_interval}MRI"]))

    if reverse_assigning:

        (
            next_app_date,
            next_appdate_interval,
            valid_next_date,
            valid_next_app_rate,
            next_app_rate_id,
            next_app_rate,
        ) = get_next_reverse_date(current_app_date, mri, ag_practices, applications)

    else:  # forward assigning
        next_forward_date = current_app_date + mri

        if next_forward_date.year > current_app_date.year:  # next forward app goes into next year
            next_forward_date = date(year=2021, month=next_forward_date.month, day=next_forward_date.day)

        next_forward_interval = get_interval(next_forward_date, ag_practices)

        next_forward_rate_id, next_forward_app_rate, valid_next_app_rate = get_rate(
            ag_practices, count, next_forward_interval, settings, next_forward_date
        )

        if valid_next_app_rate:
            # if next forward date is not valid, start reverse assigning
            if check_app_validity(
                next_forward_date,
                next_forward_interval,
                ag_practices,
                next_forward_rate_id,
                applications,
                count,
            ):
                next_app_date = next_forward_date
                next_appdate_interval = next_forward_interval
                valid_next_date = True
                next_app_rate_id = next_forward_rate_id
                next_app_rate = next_forward_app_rate

            else:  # otherwise, try a reverse date
                (
                    next_app_date,
                    next_appdate_interval,
                    valid_next_date,
                    valid_next_app_rate,
                    next_app_rate_id,
                    next_app_rate,
                ) = get_next_reverse_date(start_date, mri, ag_practices, applications)
                reverse_assigning = True

        else:
            next_app_date = pd.NA
            next_appdate_interval = pd.NA
            valid_next_date = pd.NA
            valid_next_app_rate = False
            next_app_rate_id = pd.NA
            next_app_rate = pd.NA
            reverse_assigning = pd.NA

    return (
        next_app_date,
        next_appdate_interval,
        valid_next_date,
        valid_next_app_rate,
        next_app_rate_id,
        next_app_rate,
        reverse_assigning,
    )


def adjust_app_rate(app_rate: int, appdate_interval: str, ag_practices: pd.Series, count: pd.DataFrame) -> int:
    """Reduces the application rate if the current application rate will exceed the interval amount applied
    or the total amount applied on the next application.

    Args:
        app_rate (int): application rate for the next application
        appdate_interval (str): next application date interval
        ag_practices (pd.Series): ag practices information
        count (pd.DataFrame): application limits

    Returns:
        int: potentially adjusted application rate
    """
    # If interval application can be made, but max amount exceeds interval max amount, apply what you can
    if (count.at[appdate_interval, "amt_applied"] + app_rate) > ag_practices[f"{appdate_interval}_MaxAmt_lbsacre"]:
        app_rate = ag_practices[f"{appdate_interval}_MaxAmt_lbsacre"] - count.at[appdate_interval, "amt_applied"]
    # If interval application can be made, but max amount exceeds annual max amount, apply what you can
    if (app_rate > 0) and (count.at["Total", "amt_applied"] + app_rate > ag_practices["MaxAnnAmt_lbsacre"]):
        app_rate = ag_practices["MaxAnnAmt_lbsacre"] - count.at["Total", "amt_applied"]

    return app_rate


def no_more_apps_can_be_made(count: pd.DataFrame, ag_practices: pd.Series):
    """Checks if more apps can be made. Specifically, checks if the annual
    limits are reached, all interval limits are reached, or if all rates
    are exhausted.

    Args:
        count (pd.DataFrame): application records
        ag_practices (pd.Series): run ag practices

    Returns:
        bool: True if no more apps can be made
    """

    # check PWC maximum of 50 apps per run
    if count.at["Total", "num_apps"] == 50:
        logger.warning("WARNING: The PWC maximum of 50 applications per run is reached.")
        return True

    # If maximum annual limits have been reached, we are done assigning application dates for this run
    if (count.at["Total", "num_apps"] == ag_practices["MaxAnnNumApps"]) or (
        count.at["Total", "amt_applied"] == ag_practices["MaxAnnAmt_lbsacre"]
    ):
        return True

    # check if the interval limits are reached
    # checks if either the pre-emergence num apps or amt applied is met AND
    # the post-emergence num apps or amt applied is met
    if (
        (count.at["PreEmergence", "num_apps"] == ag_practices["PreEmergence_MaxNumApps"])
        or (count.at["PreEmergence", "amt_applied"] == ag_practices["PreEmergence_MaxAmt_lbsacre"])
    ) and (
        (count.at["PostEmergence", "num_apps"] == ag_practices["PostEmergence_MaxNumApps"])
        or (count.at["PostEmergence", "amt_applied"] == ag_practices["PostEmergence_MaxAmt_lbsacre"])
    ):
        return True

    # check if the all the rates have been exausted
    exhausted_rates = []
    for i in [1, 2, 3, 4]:
        if ag_practices[f"Rate{i}_MaxAppRate_lbsacre"] != np.inf:  # rate exists
            if count.at[f"Rate{i}", "num_apps"] == ag_practices[f"Rate{i}_MaxNumApps"]:
                exhausted_rates.append(True)  # rate is exhausted
            else:
                exhausted_rates.append(False)  # rate is not exhausted
        else:
            exhausted_rates.append(True)

    if all(exhausted_rates):
        return True

    return False


def derive_instruction_date_restrictions(rate: str, run_ag_practices: pd.Series):
    """Parses the rate dependent instructions to get the instructions start date and the
    instructions end date. Adds those attributes to the run_ag_practices series.

    Args:
        rate (str): rate identifier
        run_ag_practices (pd.Series): ag practices for run

    Returns:
        instructions start date, instructions end date, boolean requirements
    """

    ops = {"+": operator.add, "-": operator.sub}
    date_ref = {"E": run_ag_practices["Emergence"], "H": run_ag_practices["Harvest"]}

    # for a given rate calculate the instructions specific date restrictions
    if pd.isna(run_ag_practices[f"{rate}_Instructions"]):  # special rate instructions are not listed
        instr_start_date = pd.NA
        instr_end_date = pd.NA
        bool_switch = pd.NA
    else:
        rate_instructions: str = run_ag_practices[f"{rate}_Instructions"]
        bool_switch, period = rate_instructions.split("_")

        if any(interval in period for interval in ["E", "H"]):  # E or H date is referenced

            if ">" in period:  # multiple references of E/H for range

                start, end = period.split(">")

                start_event = start[0]
                start_op = start[1]
                start_days = start[2:]

                end_event = end[0]
                end_op = end[1]
                end_days = end[2:]

                op1 = ops[start_op]  # first operator
                op2 = ops[end_op]  # second operator

                # calculate dates from E/H date, operator, and day interval
                instr_start_date = op1(date_ref[start_event], timedelta(days=int(start_days)))
                instr_end_date = op2(date_ref[end_event], timedelta(days=int(end_days)))

            else:  # single reference of E/H for range
                if period[1] == "-":
                    instr_start_date = date_ref[period[0]] - timedelta(days=int(period[2:]))
                    instr_end_date = date_ref[period[0]]
                else:
                    instr_start_date = date_ref[period[0]]
                    instr_end_date = date_ref[period[0]] + timedelta(days=int(period[2:]))

        else:  # specific date range specified
            instr_start_date = date(year=2021, month=int(period[:2]), day=int(period[2:4]))
            instr_end_date = date(year=2021, month=int(period[5:7]), day=int(period[-2:]))

        # reassign date limits to reference 2021 year
        if instr_start_date.year != 2021:
            instr_start_date = date(year=2021, month=instr_start_date.month, day=instr_start_date.day)
        if instr_end_date.year != 2021:
            instr_end_date = date(year=2021, month=instr_end_date.month, day=instr_end_date.day)

    return instr_start_date, instr_end_date, bool_switch


def meets_instruction_constraints(app_date: date, ag_practices: pd.Series, rate: str) -> bool:
    """Tests if the application dates satisfies the rate specific instruction constraints.

    Args:
        app_date (date): potential application date
        ag_practices (pd.Series): ag practices information
        rate (str): current application rate

    Returns:
        bool: True if app satisfies instruction constraints
    """

    if ag_practices[f"{rate}_Instructions"] == np.inf:
        return True

    if ag_practices[f"{rate}_instr_timeframe"] == "Y":  # applications must be made between start and end date

        # if ISD is before IED (same year)
        if ag_practices[f"{rate}_instr_startdate"] < ag_practices[f"{rate}_instr_enddate"]:
            return bool(ag_practices[f"{rate}_instr_startdate"] <= app_date <= ag_practices[f"{rate}_instr_enddate"])

        # IED is before ISD (different year)
        start_date_1 = date(year=2021, month=1, day=1)  # first day of the year
        end_date_1 = ag_practices[f"{rate}_instr_enddate"]

        start_date_2 = ag_practices[f"{rate}_instr_startdate"]
        end_date_2 = date(year=2021, month=12, day=31)

        return bool(start_date_1 <= app_date <= end_date_1 or start_date_2 <= app_date <= end_date_2)

    # applications cannot be made between start and end date
    # if ISD is before IED (same year)
    if ag_practices[f"{rate}_instr_startdate"] < ag_practices[f"{rate}_instr_enddate"]:

        return bool(not (ag_practices[f"{rate}_instr_startdate"] <= app_date <= ag_practices[f"{rate}_instr_enddate"]))

    # IED is before ISD (different year)
    start_date_1 = date(year=2021, month=1, day=1)  # first day of the year
    end_date_1 = ag_practices[f"{rate}_instr_enddate"]

    start_date_2 = ag_practices[f"{rate}_instr_startdate"]
    end_date_2 = date(year=2021, month=12, day=31)

    return bool(not (start_date_1 <= app_date <= end_date_1 or start_date_2 <= app_date <= end_date_2))


def within_mri(new_app: date, applications: list[tuple[date, float]], mri: int) -> bool:
    """Checks if an application date violates the MRI.

    Compares the new_app date to applications already made and if the new
    application is within the MRI, returns True.

    Args:
        new_app (date): Date of application to check
        applications (list[tuple[date, float]]): List of applications already made
        mri (int): Minimum reapplication interval

    Returns:
        bool: True if app_date is within the MRI of an application already made,
            otherwise False
    """
    for app_date, __ in applications:
        if abs(app_date - new_app) < timedelta(days=mri):
            return True

    return False


def within_phi(app_date: date, appdate_interval: str, ag_practices: pd.Series) -> bool:
    """Tests if date is within the pre harvest interval.

    Args:
        app_date (date): potential application date
        appdate_interval (str): interval that the application is in
        ag_practices (pd.Series): ag practices information for run

    Returns:
        bool: True if within the PHI, False if not
    """

    if appdate_interval == "PreEmergence":  # app cannot be day before emergence date
        return bool(app_date == ag_practices["Emergence"] - timedelta(days=1))
    # post emergence, app cannot be applied within PHI
    return bool(
        (ag_practices["Harvest"] - timedelta(days=int(ag_practices["PHI"]))) < app_date <= ag_practices["Harvest"]
    )


def random_start_dates(random_start_date: bool) -> str:
    """Derives the random start date identifier for the run descriptor.
    Is either yes random start date or no random start date.

    Args:
        random_start_date (bool): run configuration

    Returns:
        str: string for run descriptor
    """

    if random_start_date is True:
        rsd_str = "rd"
    else:
        rsd_str = "nrd"

    return rsd_str


def date_prioritization(date_prior: str) -> str:
    """Derives the date prioritization indicator for the run descriptor.
    Date prioritization is either max app rate or wettest months.

    Args:
        date_prior (str): run configuration

    Returns:
        str: date prioritization identifier
    """

    if date_prior == "Max App. Rate":
        date_prior_str = "pma"
    else:
        date_prior_str = "pwm"

    return date_prior_str
