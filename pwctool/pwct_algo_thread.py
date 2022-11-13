"""App Date tool module specifically for gui execution, OOP version"""

from datetime import date
import time
import logging
from operator import itemgetter
import os
import linecache
import random
import sys
import calendar
from typing import Any

import pandas as pd
import numpy as np
from PyQt5 import QtCore as qtc

from pwctool.pwct_batchfile_qc import qc_batch_file
from pwctool.pwct_algo_functions import lookup_huc_from_state
from pwctool.pwct_algo_functions import get_all_potential_app_dates
from pwctool.pwct_algo_functions import get_interval
from pwctool.pwct_algo_functions import get_rate
from pwctool.pwct_algo_functions import check_app_validity
from pwctool.pwct_algo_functions import prepare_next_app
from pwctool.pwct_algo_functions import adjust_app_rate
from pwctool.pwct_algo_functions import no_more_apps_can_be_made
from pwctool.pwct_algo_functions import derive_instruction_date_restrictions
from pwctool.pwct_algo_functions import random_start_dates
from pwctool.pwct_algo_functions import date_prioritization

logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py


class AdtAlgoThread(qtc.QThread):
    """Class for the app date tool algorithm thread"""

    update_diagnostics = qtc.pyqtSignal(str)
    update_progress = qtc.pyqtSignal(float)

    def __init__(self, settings: dict[str, Any]) -> None:
        super().__init__()

        self.settings = settings
        self._scenarios: dict[str, tuple[date, date]] = {}
        self._error_max_amt: list[str] = []
        self._error_scn_file_notexist: list[str] = []

    def run(self):
        """Manages app date tool algorithm components
        run is a method of QThread which is automatically executed
        upon calling .start() method from the isntantiated worker.
        """
        self.update_diagnostics.emit("\nInitializing...")

        # create new batch file
        if self.settings["USE_CASE"] == "Use Case #1":
            logger.debug("Preparing to generate PWC batch file from scratch.")
            self.update_diagnostics.emit("Preparing to generate PWC batch file from scratch.")

            # read relavent tables
            ag_practices_table = self.read_ag_practices_table()
            drift_reduction_table = self.read_drift_reduction_table()
            wettest_month_table = self.read_wettest_month_table()
            ingredient_fate_params_table = self.read_ingredient_fate_parameters_table()
            state_to_huc_lookup_table = self.read_state_to_huc_lookup_table()
            bin_to_landsape_params_lookup_table = self.read_bin_to_landscape_lookup_table()

            self.generate_batch_file_from_scratch(
                ag_practices_table,
                drift_reduction_table,
                wettest_month_table,
                ingredient_fate_params_table,
                state_to_huc_lookup_table,
                bin_to_landsape_params_lookup_table,
            )

        # QC existing batch file
        else:

            # read relavent tables
            input_pwc_batch_file = self.read_input_pwc_batch_file()
            ag_practices_table = self.read_ag_practices_table()
            drift_reduction_table = self.read_drift_reduction_table()

            self.quality_check_batch_file(input_pwc_batch_file, ag_practices_table, drift_reduction_table)

    #### READ INPUT TABLES ####

    def read_input_pwc_batch_file(self) -> pd.DataFrame:
        """Reads the input pwc batch file.
        Only keep rows that are relavent
        (i.e., match HUC2s and aquatic bins
        specified in GUI)

        Returns:
            pd.DataFrame: input pwc batch file
        """
        try:
            input_pwc_batch_file: pd.DataFrame = pd.read_csv(self.settings["FILE_PATHS"]["PWC_BATCH_CSV"])
        except FileNotFoundError:
            logger.error("\n ERROR: The PWC batch file was not found. Please check the path in the config file.")
            self.update_diagnostics.emit(
                "\n ERROR: The PWC batch file was not found. Please check the path in the config file."
            )
        return input_pwc_batch_file

    def read_ag_practices_table(self) -> pd.DataFrame:
        """Reads the ag practices table.

        Returns:
            pd.DataFrame: ag practices table
        """

        def get_ag_practices(apt: pd.ExcelFile, scenario: str) -> pd.DataFrame:
            """Reads compound specific ag practice data from Excel Ag Practices Table (APT).

            Args:
                apt (pd.ExcelFile): The Ag Practices Table (APT) from the config file
                scenario (str): Name of the worksheet to extract from the APT

            Returns:
                pd.DataFrame: Scenario-specific ag practices
            """
            try:
                ag_practices = pd.read_excel(apt, sheet_name=scenario, index_col="RunDescriptor")
            except FileNotFoundError:
                logger.error(f"\nERROR: APT '{apt}' not found, " "please check the filename in the config file.\n\n")
                self.update_diagnostics.emit(
                    f"\nERROR: APT '{apt}' not found, " "please check the filename in the config file.\n\n"
                )
                raise
            except ValueError:
                logger.error(
                    f"\nERROR: get_ag_practices() Worksheet '{scenario}' not found in APT, "
                    "please check the sheet name in the config file.\n\n"
                )
                self.update_diagnostics.emit(
                    f"\nERROR: get_ag_practices() Worksheet '{scenario}' not found in APT, "
                    "please check the sheet name in the config file.\n\n"
                )
                raise

            return ag_practices

        try:
            ag_practices_excel_obj = pd.ExcelFile(
                self.settings["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"], engine="openpyxl"
            )
            ag_practices_table = get_ag_practices(ag_practices_excel_obj, self.settings["APT_SCENARIO"])
        except FileNotFoundError:
            logger.error("\n ERROR: The ag practices file was not found. Please check the path in the config file.")
            self.update_diagnostics.emit(
                "\n ERROR: The ag practices file was not found. Please check the path in the config file."
            )
            raise

        return ag_practices_table

    def read_drift_reduction_table(self) -> pd.DataFrame:
        """Reads the drift reduction table.

        Returns:
            pd.DataFrame: drift reduction table
        """

        # read the drift reduction table
        try:
            drift_reduction_table = pd.read_excel(
                self.settings["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"],
                sheet_name=self.settings["DRT_SCENARIO"],
                index_col="Profile",
            )
        except FileNotFoundError:
            logger.error("\n ERROR: The lookup table was not found. Please check the path in the config file.")
            self.update_diagnostics.emit(
                "\n ERROR: The lookup table was not found. Please check the path in the config file."
            )
            raise

        return drift_reduction_table

    def read_wettest_month_table(self) -> pd.DataFrame:
        """Reads the wettest month table.

        Returns:
            pd.DataFrame: wettest month table
        """

        try:
            wettest_month_table = pd.read_csv(self.settings["FILE_PATHS"]["WETTEST_MONTH_CSV"], index_col="HUC2")
        except FileNotFoundError:
            logger.error("ERROR: The wettest months table was not found. Please check the path in the config file.")
            self.update_diagnostics.emit(
                "ERROR: The wettest months table was not found. Please check the path in the config file."
            )
            raise

        return wettest_month_table

    def read_ingredient_fate_parameters_table(self) -> pd.DataFrame:
        """Reads the ingredient fate parameters table.

        Returns:
            pd.DataFrame: ingredient fate parameters table
        """
        try:
            ingred_fate_param_table = pd.read_csv(self.settings["FILE_PATHS"]["INGR_FATE_PARAMS"])
        except FileNotFoundError:
            logger.error(
                "\n ERROR: The ingredient fate parameters table was not found. Please check the path in the config file."
            )
            self.update_diagnostics.emit(
                "\n ERROR: The ingredient fate parameters table was not found. Please check the path in the config file."
            )
            raise

        return ingred_fate_param_table

    def read_state_to_huc_lookup_table(self) -> pd.DataFrame:
        """Reads the state to huc lookup table

        Returns:
            pd.DataFrame: state to huc lookup table
        """
        try:
            state_to_huc_lookup_table = pd.read_excel(self.settings["FILE_PATHS"]["STATE_TO_HUC"], index_col="STATE")
        except FileNotFoundError:
            logger.error(
                "\n ERROR: The state to huc lookup table was not found. Please check the path in the config file."
            )
            self.update_diagnostics.emit(
                "\n ERROR: The state to huc lookup table was not found. Please check the path in the config file."
            )
            raise

        return state_to_huc_lookup_table

    def read_bin_to_landscape_lookup_table(self) -> pd.DataFrame:
        """Reads the bin to landscape lookup table

        Returns:
            pd.DataFrame: bin to landscape lookup table
        """
        try:
            bin_to_landscape_lookup_table = pd.read_csv(
                self.settings["FILE_PATHS"]["BIN_TO_LANDSCAPE"], index_col="Bin"
            )
        except FileNotFoundError:
            logger.error(
                "\n ERROR: The bin to landscape lookup table was not found. Please check the path in the config file."
            )
            self.update_diagnostics.emit(
                "\n ERROR: The bin to landscape lookup table was not found. Please check the path in the config file."
            )
            raise

        return bin_to_landscape_lookup_table

    #### QC BATCH FILE ####

    def quality_check_batch_file(
        self, input_pwc_batch_file: pd.DataFrame, ag_practices_table: pd.DataFrame, drift_reduction_table: pd.DataFrame
    ):
        """QCs the batch file. Does not update anything. Writes results/log file to output dir."""

        logger.info("Quality checking input PWC batch file...")
        self.update_diagnostics.emit("\nQuality checking input PWC batch file...")

        qc_results = qc_batch_file(
            input_pwc_batch_file, ag_practices_table.copy(deep=True), drift_reduction_table, self.settings
        )
        self.update_progress.emit(100)

        qc_results_output = pd.DataFrame.from_dict(data=qc_results, orient="columns")

        # create final pass/fail column, pass if everything is within label restrictions
        check_columns = [col for col in qc_results_output.columns if "Check" in col]
        qc_results_output.insert(loc=0, column="RunisValid", value=qc_results_output[check_columns].eq(True).all(1))

        qc_results_output.to_csv(
            os.path.join(self.settings["FILE_PATHS"]["OUTPUT_DIR"], f"{self.settings['RUN_ID']} QC Results.csv"),
            index=False,
        )

        logger.info("\nCheck the output directory for a full QC report.")
        self.update_diagnostics.emit("Check the output directory for a full QC report.")

    ### GENERATE BATCH FILE FROM SCRATCH ####

    def generate_batch_file_from_scratch(
        self,
        ag_practices_table: pd.DataFrame,
        drift_reduction_table: pd.DataFrame,
        wettest_month_table: pd.DataFrame,
        ingredient_fate_params_table: pd.DataFrame,
        state_to_huc_lookup_table: pd.DataFrame,
        bin_to_landsape_params_lookup_table: pd.DataFrame,
    ):
        """Generates batch file from scratch. Uses the ag practices table,
        the GUI, and other input tables to generate a batch file. Uses the
        date assignment algorithm to assign dates

        Stores final table in a list of dictionaries, where each dictionary
        is a single run. Runs (rows) are created by iterating through the
        ag practices table and all other run parameters.

        Args:
            ag_practices_table (pd.DataFrame): ag practices table
            drift_reduction_table (pd.DataFrame): drift reduction table
            wettest_month_table (pd.DataFrame): wettest month table
            ingredient_fate_params_table (pd.DataFrame): ingredient to fate params table
            state_to_huc_lookup_table (pd.DataFrame): state to huc lookup table
            bin_to_landsape_params_lookup_table (pd.DataFrame): bin to landscape params lookup table
        """

        start_time = time.time()  # start timer
        store_all_runs: list[dict[str, Any]] = []
        ingred_fate_params = dict(zip(ingredient_fate_params_table["Parameter"], ingredient_fate_params_table["Value"]))

        # convert lbs/acre to kg/ha for all rate fields
        ag_practices_table["MaxAnnAmt"] = ag_practices_table["MaxAnnAmt"] * 1.120851  # convert from lbs/ac to kg/ha
        ag_practices_table["PostEmergence_MaxAmt"] = ag_practices_table["PostEmergence_MaxAmt"] * 1.120851
        ag_practices_table["PreEmergence_MaxAmt"] = ag_practices_table["PreEmergence_MaxAmt"] * 1.120851
        ag_practices_table["Rate1_MaxAppRate"] = ag_practices_table["Rate1_MaxAppRate"] * 1.120851
        ag_practices_table["Rate2_MaxAppRate"] = ag_practices_table["Rate2_MaxAppRate"] * 1.120851
        ag_practices_table["Rate3_MaxAppRate"] = ag_practices_table["Rate3_MaxAppRate"] * 1.120851
        ag_practices_table["Rate4_MaxAppRate"] = ag_practices_table["Rate4_MaxAppRate"] * 1.120851

        # prepare for blank fields
        blank_fields = {}
        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
            blank_fields[f"blank {i}"] = pd.NA

        # prepare for progress updates
        total_rows_in_apt = len(ag_practices_table.index)
        ag_practices_table.reset_index(inplace=True)

        # iterate through each row in the apt
        num_runs = 0
        for apt_row_num, run_ag_pract in ag_practices_table.iterrows():
            self.update_progress.emit((int(apt_row_num) / total_rows_in_apt) * 100)

            huc2s = lookup_huc_from_state(state_to_huc_lookup_table, run_ag_pract)
            application_method = run_ag_pract["ApplicationMethod"]
            run_distances = self.settings["APP_DISTANCES"][application_method]

            for huc2 in huc2s:
                scenario_base = f"{run_ag_pract['Scenario']}{huc2}"
                scenario_full = f"{scenario_base}.scn"

                if not os.path.exists(os.path.join(self.settings["FILE_PATHS"]["SCENARIO_FILES_PATH"], scenario_full)):
                    self._error_scn_file_notexist.append(scenario_base)
                    logger.warning(f"\n {scenario_base} may not exist. Skipping huc {huc2}")
                    continue

                # report to log file
                logger.debug("\nRun Descriptor: %s", run_ag_pract["RunDescriptor"])
                logger.debug("Application Method: %s", application_method)
                logger.debug("Valid states: %s", run_ag_pract["States"])
                logger.debug("HUC2: %s", huc2)
                logger.debug("Bins to process: %s", self.settings["BINS"])
                logger.debug("Distances to process: %s", run_distances)
                logger.debug("Transport mechanisms: %s", self.settings["EXPOSURE_TYPES"])
                logger.debug("Date prioritization: %s", self.settings["DATE_PRIORITIZATION"])
                logger.debug("Random start dates: %s", self.settings["RANDOM_START_DATES"])
                if self.settings["RANDOM_START_DATES"]:
                    logger.debug("Random Seed: %s", self.settings["RANDOM_SEED"])

                # get emergence and harvest date
                run_ag_pract["Emergence"], run_ag_pract["Harvest"] = self.get_scenario_dates(scenario_full)

                first_run = True
                run_ag_pract.replace(to_replace=np.inf, value=pd.NA, inplace=True)

                # interval validity is rate dependent and valid if MRI value is specified rate
                for rate in ["Rate1", "Rate2", "Rate3", "Rate4"]:
                    rate_valid_intervals = []
                    if pd.notna(run_ag_pract[f"{rate}_PreEmergenceMRI"]):
                        rate_valid_intervals.append("PreEmergence")
                    if pd.notna(run_ag_pract[f"{rate}_PostEmergenceMRI"]):
                        rate_valid_intervals.append("PostEmergence")
                    if len(rate_valid_intervals) == 0:
                        rate_valid_intervals.append(pd.NA)  # use nan to indicate no valid intervals
                    run_ag_pract[f"{rate}_ValidIntervals"] = rate_valid_intervals

                    # redive special date istructions (dependent on emergence and harvest dates)
                    (
                        run_ag_pract[f"{rate}_instr_startdate"],
                        run_ag_pract[f"{rate}_instr_enddate"],
                        run_ag_pract[f"{rate}_instr_timeframe"],
                    ) = derive_instruction_date_restrictions(rate, run_ag_pract)

                for bin_ in self.settings["BINS"]:
                    try:
                        landscape_params = (
                            bin_to_landsape_params_lookup_table.loc[int(bin_), :].copy(deep=True).to_dict()
                        )
                    except KeyError:
                        logger.warning(f"\n ERROR: bin {bin_} may not be in the bin to landscape params table.")
                        logger.warning(f" Skipping all bin {bin_} runs...")
                        # self.update_diagnostics.emit(
                        #    f"\nWARNING: bin {bin_} may not be in the bin to landscape params table."
                        # )
                        # self.update_diagnostics.emit(f"Skipping all bin {bin_} runs...")
                        continue

                    for distance in run_distances:
                        drift_profile_bin = f"{bin_}-{run_ag_pract['DriftProfile']}"
                        try:
                            drift_value = drift_reduction_table.at[drift_profile_bin, distance]
                            eff = drift_reduction_table.at[drift_profile_bin, "Efficiency"]
                        except KeyError:
                            logger.warning(f"\n ERROR: drift profile {drift_profile_bin} may not be in the DRT.")
                            logger.warning(f" Skipping all bin {drift_profile_bin} runs...")
                            # self.update_diagnostics.emit(
                            #    f"\nWARNING: drift profile {drift_profile_bin} may not be in the DRT."
                            # )
                            # self.update_diagnostics.emit(f"Skipping all bin {drift_profile_bin} runs...")
                            continue

                        for app_type in self.settings["EXPOSURE_TYPES"][distance]:  # RD or D

                            if first_run:
                                logger.debug("\nRun Ag. Practices:")
                                logger.debug(run_ag_pract)

                            run_storage: dict[str, Any] = {}  # new run (row) in batch file

                            run_storage["Run Descriptor"] = run_ag_pract["RunDescriptor"]
                            run_name = f"{run_ag_pract['RunDescriptor']}_{huc2}_{application_method}_{scenario_base}_{bin_}_{distance}_{app_type}"
                            run_ag_pract["RunName"] = run_name
                            self.update_diagnostics.emit(f"Processing run: {run_name}")
                            run_storage["Run Name"] = run_name

                            run_storage.update(ingred_fate_params)

                            run_storage["HUC2"] = huc2
                            run_storage["Scenario"] = scenario_full

                            run_storage["weather overide"] = pd.NA
                            run_storage.update(blank_fields)

                            run_storage["AquaticBin"] = bin_
                            run_storage.update(landscape_params)

                            run_storage["Num_Daysheds"] = 1
                            run_storage["IRF1"] = 1
                            for irf in np.arange(2, 32):
                                run_storage[f"IRF{irf}"] = 0

                            applications = self.assign_application_dates(
                                wettest_month_table, run_ag_pract, huc2, first_run
                            )

                            run_storage["NumberofApplications"] = len(applications)
                            run_storage["Absolute Dates?"] = "TRUE"
                            run_storage["Relative Dates?"] = pd.NA

                            for app_num, (app_date, app_rate) in enumerate(applications):

                                run_storage[f"Day{app_num+1}"] = app_date.day
                                run_storage[f"Month{app_num+1}"] = app_date.month
                                run_storage[f"AppRate (kg/ha){app_num+1}"] = app_rate
                                run_storage[f"Eff.{app_num+1}"] = eff
                                run_storage[f"Drift{app_num+1}"] = drift_value

                            store_all_runs.append(run_storage)  # store run values

                            first_run = False
                            num_runs += 1

        self.update_progress.emit(100)

        # write new batch file to output csv
        new_batch_file = pd.DataFrame(store_all_runs)
        new_batch_file.to_csv(
            os.path.join(self.settings["FILE_PATHS"]["OUTPUT_DIR"], f"{self.settings['RUN_ID']}_new_batch_file.csv"),
            index=False,
        )

        # report any errors
        if len(self._error_max_amt) > 0:
            logger.warning("\n WARNING: The maximum annual amount was not reached for the following runs:")
            logger.warning(set(self._error_max_amt))
            logger.warning("\n For these runs, please ensure the agronomic practices table (APT) is correct.")
            logger.warning(" If the APT is correct, and random dates is turned on, it may be")
            logger.warning(" that the random date selection is preventing all possible apps")
            logger.warning(" from being made. You can try again or turn random dates off.")

            self.update_diagnostics.emit("\n WARNING: The maximum annual amount was not reached for some runs.")
            self.update_diagnostics.emit(" Please check the log file for a full error report.")

        if len(self._error_scn_file_notexist) > 0:
            logger.warning("\n WARNING: Scenario files may not exist for the following crop-huc pairs:")
            logger.warning(set(self._error_scn_file_notexist))
            logger.warning("\n In these cases, the runs associated with that crop-HUC2 pair were skipped.")

            self.update_diagnostics.emit("\n WARNING: Scenario files may not exist for some crop-huc pairs.")
            self.update_diagnostics.emit(" Please check the log file for a full error report.")

        # report excecution time
        execution_time = str(round(time.time() - start_time, 1))
        logger.debug("\n%s runs generated", num_runs)
        logger.debug("Execution time (seconds): %s", execution_time)

        self.update_diagnostics.emit(f"\nFinished! {num_runs} Runs generated in {execution_time} seconds.")
        self.update_diagnostics.emit(
            "Please check the output directory for the log file which contains a full processing report."
        )

    def get_scenario_dates(
        self,
        scenario: str,
    ) -> tuple[date, date]:
        """Extracts emergence and harvest dates from a scenario file.
        Args:
            scenario (str): Name of the scenario assigned to the run being processed
        Returns:
            tuple[date, date]: emergence and harvest dates for the run
                from the EPA scenario
        """
        if scenario in self._scenarios:
            # Scenario has already been processed, return stored dates
            emergence_date, harvest_date = self._scenarios[scenario]
        else:
            scenario_file = os.path.join(self.settings["FILE_PATHS"]["SCENARIO_FILES_PATH"], scenario)
            # extract date information from specific lines in .scn files
            emergence_day = int(linecache.getline(scenario_file, 28))
            emergence_month = int(linecache.getline(scenario_file, 29))
            harvest_day = int(linecache.getline(scenario_file, 32))
            harvest_month = int(linecache.getline(scenario_file, 33))
            # use arbitrary year that is not a leap year to complete the date
            emergence_date = date(year=2021, month=emergence_month, day=emergence_day)
            harvest_date = date(year=2021, month=harvest_month, day=harvest_day)
            self._scenarios[scenario] = (emergence_date, harvest_date)
        return emergence_date, harvest_date

    def assign_application_dates(
        self, wettest_month_table: pd.DataFrame, ag_practices: pd.Series, huc2: str, first_run: bool
    ) -> list[tuple[date, float]]:
        """Assign application dates for a run.

        Assigns application dates until the rate specific, interval, and / or annual
        limits are reached. Each application uses the maximum rate allowed unless it
        will exceed the interval or annual total amount limit, in which case the last
        application will be at a rate that will equal the annual total amount
        limit. Applications are applied using the highest rates first, and follow
        special instructions if specified.

        Example:  Max. Rate = 2 lbs AI / Acre, Ann. Max Amt = 5 lbs. AI / Acre
                App #1 = 2 lbs., App #2 = 2 lbs., App #3 = 1 lb.

        Args:
            wettest_month_table (pd.DataFrame): DataFrame with ranked wettest month information
            ag_practices (pd.Series): Series containing agronomic practices information
                for the run
            huc2 (str): huc2 identifier
            first_run (bool): indicates first base run
        Returns:
            list[tuple[date, float]]: Application dates for the run
        """

        # track number of apps and amount applied for all "levels" of constraints
        cols = ["num_apps", "amt_applied"]
        rows = ["Total", "PreEmergence", "PostEmergence", "Rate1", "Rate2", "Rate3", "Rate4"]
        count = pd.DataFrame(0.0, index=rows, columns=cols)

        # list of assigned application dates and amount applied on each date
        applications: list[tuple[date, float]] = []

        # use np.inf (i.e., no limit) for unspecified constraints
        ag_practices.replace(to_replace=pd.NA, value=np.inf, inplace=True)

        potential_app_dates = get_all_potential_app_dates(wettest_month_table, huc2, first_run)

        loop_count = 0
        apps_can_be_made = True
        while apps_can_be_made:
            for potential_date in potential_app_dates:

                start_date = self.get_start_date(potential_date)
                appdate_interval = get_interval(start_date, ag_practices)
                rate_id, app_rate, valid_app_rate = get_rate(
                    ag_practices, count, appdate_interval, self.settings, start_date
                )
                valid_start_date = check_app_validity(
                    start_date, appdate_interval, ag_practices, rate_id, applications, count
                )

                app_date = start_date
                reverse_assigning = False
                valid_next_date = True

                # Make applications as long as all conditions are met
                while (
                    (valid_start_date)
                    and (valid_app_rate)
                    and (valid_next_date)
                    and (app_rate > 0)
                    and (count.at[rate_id, "num_apps"] + 1 <= ag_practices[f"{rate_id}_MaxNumApps"])
                    and (count.at["Total", "num_apps"] + 1 <= ag_practices["MaxAnnNumApps"])
                    and (count.at["Total", "amt_applied"] + app_rate <= ag_practices["MaxAnnAmt"])
                ):
                    # add application to the list and update counts
                    applications.append((app_date, app_rate))
                    count.at[rate_id, "num_apps"] += 1
                    count.at[rate_id, "amt_applied"] += app_rate
                    count.at[appdate_interval, "num_apps"] += 1
                    count.at[appdate_interval, "amt_applied"] += app_rate
                    count.at["Total", "num_apps"] += 1
                    count.at["Total", "amt_applied"] += app_rate

                    (
                        app_date,
                        appdate_interval,
                        valid_next_date,
                        valid_app_rate,
                        rate_id,
                        app_rate,
                        reverse_assigning,
                    ) = prepare_next_app(
                        app_date,
                        appdate_interval,
                        rate_id,
                        start_date,
                        reverse_assigning,
                        ag_practices,
                        applications,
                        count,
                        self.settings,
                    )

                    if valid_app_rate:
                        app_rate = adjust_app_rate(app_rate, appdate_interval, ag_practices, count)

                if no_more_apps_can_be_made(count, ag_practices):
                    apps_can_be_made = False
                    break

            loop_count += 1
            if loop_count == 5:
                apps_can_be_made = False

        if first_run:
            logger.debug("\nApplications:")
            # self.update_diagnostics.emit("\nApplications:")
            for app_date, rate in applications:
                logger.debug(f"   {app_date:%m-%d} @ {rate:0.2f} lbs. AI / acre")
                # self.update_diagnostics.emit(f"   {app_date:%m-%d} @ {rate:0.2f} lbs. AI / acre")

            logger.debug(f"\nFinal Totals:\n{count}")
            # self.update_diagnostics.emit(f"\nFinal Totals:\n{count}")

            if count.at["Total", "amt_applied"] < ag_practices["MaxAnnAmt"]:
                logger.warning(
                    f"\n WARNING: Annual maximum application amount of {ag_practices['MaxAnnAmt']} lbs. AI/Acre not applied."
                )
                logger.warning(" Please ensure the agronomic practices table (APT) is correct.")
                logger.warning(" If the APT is correct, and random dates is turned on, it may be")
                logger.warning(" that the random date selection is preventing all possible apps")
                logger.warning(" from being made. You can try again or turn random dates off.")

                self._error_max_amt.append(ag_practices["RunName"])

        return applications

    def get_start_date(self, potential_date: date):
        """Selects a random start date if random start dates is turned on"""

        _, num_days_in_month = calendar.monthrange(2021, potential_date.month)

        if self.settings["RANDOM_START_DATES"]:

            if self.settings["RANDOM_SEED"] != "":  # random seed specified
                try:
                    random.seed(self.settings["RANDOM_SEED"])
                except ValueError:
                    logger.critical("\n ERROR: The random seed that was specified is not a valid type")
                    logger.critical(" The valid types are integer, float, string, or leave it blank.")
                    # self.update_diagnostics.emit("\nERROR: The random seed that was specified is not a valid type")
                    # self.update_diagnostics.emit(" The valid types are integer, float, string, or leave it blank.")
                    sys.exit()

            return date(
                year=2021,
                month=potential_date.month,
                day=random.randint(1, num_days_in_month),
            )

        return potential_date

    def get_ranked_month_info(self, huc: str, wettest_months: pd.DataFrame) -> pd.DataFrame:
        """Gets rank and date of month.

        The months are ranked by rainfall amount based on the wettest months table.
        The new table is a DataFrame with wettest month rankings the date of the
        first day of each month.

        Args:
            huc (str): HUC2 for the run
            wettest_months (pd.DataFrame): Wettest months table

        Returns:
            pd.DataFrame: Ranked month information with interval specific
                wettest months for all intervals
        """
        ranks: list[str] = []  # list of ranks to use for the index of the final dataframe
        current_month: dict[str, Any] = {}  # single month's data
        months = []  # list of month data to create the dataframe

        for month_rank in wettest_months:
            # Initialize start date for the month to the 1st
            current_month["date"] = date(year=2021, month=wettest_months.at[f"{huc}", month_rank], day=1)
            ranks.append(month_rank)
            months.append(current_month.copy())

        ranked_month_info = pd.DataFrame(months, index=ranks)
        logger.debug(f"\nWettest Months:\n{ranked_month_info.to_string()}")

        return ranked_month_info

    def application_method(self, ag_practices: pd.Series) -> str:
        """Determines the application method.

        Returns a string (aerial, granular or ground) indicating the type of application made
        based on the drift profile for the run.

        Args:
            ag_practices (pd.Series): Ag practices information for the run

        Returns:
            str: The application method (aerial, granular or ground)
        """
        if ag_practices["DriftProfile"].startswith("A-"):
            app_method = "aerial"
        elif ag_practices["DriftProfile"] == "G-GRAN":
            app_method = "granular"
        elif ag_practices["DriftProfile"].startswith(("G-", "AB-")):
            app_method = "ground"
        else:
            logger.error(f"\n ERROR unknown drift profile name '{ag_practices['DriftProfile']}' in APT.")
            logger.error(" Please check drift profile table to ensure the drift profile is correct.")
            # self.update_diagnostics.emit(
            #    f"\n ERROR unknown drift profile name '{ag_practices['DriftProfile']}' in APT."
            # )
            # self.update_diagnostics.emit(f" Please check drift profile table to ensure the drift profile is correct.")
            raise ValueError

        return app_method
