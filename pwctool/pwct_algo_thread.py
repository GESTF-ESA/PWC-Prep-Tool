"""
Algorithm thread module

Called when "run" button is pressed
"""

import time
import logging
import os
import linecache
import random
import sys
import calendar
from datetime import date
from typing import Any, Union

from PyQt5 import QtCore as qtc

import pandas as pd
import numpy as np

# import debugpy

from pwctool.pwct_batchfile_qc import qc_batch_file  # pylint: disable=import-error
from pwctool.pwct_batchfile_qc import standardize_field_names  # pylint: disable=import-error
from pwctool.pwct_algo_functions import lookup_states_from_crop  # pylint: disable=import-error
from pwctool.pwct_algo_functions import get_drift_profile  # pylint: disable=import-error
from pwctool.pwct_algo_functions import lookup_huc_from_state  # pylint: disable=import-error
from pwctool.pwct_algo_functions import get_interval  # pylint: disable=import-error
from pwctool.pwct_algo_functions import get_rate  # pylint: disable=import-error
from pwctool.pwct_algo_functions import check_app_validity  # pylint: disable=import-error
from pwctool.pwct_algo_functions import prepare_next_app  # pylint: disable=import-error
from pwctool.pwct_algo_functions import adjust_app_rate  # pylint: disable=import-error
from pwctool.pwct_algo_functions import no_more_apps_can_be_made  # pylint: disable=import-error
from pwctool.pwct_algo_functions import derive_instruction_date_restrictions  # pylint: disable=import-error

from pwctool.constants import (
    ALL_APPMETHODS,
    BURIED_APPMETHODS,
    ALL_DISTANCES,
    FOLIAR_APPMETHOD,
)

logger = logging.getLogger("adt_logger")  # retrieve logger configured in app_dates.py

# fmt: off
CROP_TO_STATE_LUT:dict[str,list] = {
    "ALMONDS":	"AL,AZ,AR,CA,CO,FL,GA,IL,KY,MS,MO,NM,OH,SC,TN,TX,UT,VA,WA",
    "APPLES":	"AL,AK,AZ,AR,CA,CO,CT,FL,GA,HI,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "APRICOTS":	"AL,AZ,AR,CA,CO,GA,HI,ID,IL,IA,KS,KY,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VA,WA,WV,WI",
    "ARONIA BERRIES":	"CA,IL,IA,KS,KY,MD,MA,MI,MN,MO,MT,NE,NJ,NC,ND,OH,OR,PA,SD,TN,VT,VA,WA,WI",
    "ARTICHOKES":	"AZ,CA,CO,HI,MD,MA,MN,MO,NH,NM,NY,NC,OH,OR,SC,TX,VT,VA,WA,WI",
    "ASPARAGUS":	"AL,AK,AZ,AR,CA,CO,CT,FL,GA,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "AVOCADOS":	"CA,FL,HI,LA,TX",
    "BANANAS":	"CA,FL,HI,SC,TX",
    "BARLEY":	"AL,AK,AZ,CA,CO,CT,DE,GA,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MO,MT,NE,NV,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "BEANS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "BEANS, DRY EDIBLE, (EXCL CHICKPEAS & LIMA)":	"AZ,CA,CO,HI,ID,IL,KS,ME,MA,MI,MN,MT,NE,NV,NM,NY,NC,ND,OH,OK,OR,SD,TX,VT,VA,WA,WI,WY",
    "BEETS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "BLACKBERRIES":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "BLUEBERRIES":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,OH,OK,OR,PA,RI,SC,SD,TN,TX,VT,VA,WA,WV,WI",
    "BOYSENBERRIES":	"CA,NJ,NY,OR,PA,SC,TN,TX,UT,WA",
    "BROCCOLI":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "BRUSSELS SPROUTS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MO,MT,NE,NJ,NM,NY,NC,OH,OR,PA,RI,SC,SD,TN,TX,VT,VA,WV,WI",
    "BUCKWHEAT":	"ID,IL,IA,ME,MI,MN,MO,MT,NE,NJ,NY,ND,OH,OR,PA,SD,WA,WI",
    "CABBAGE":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CAMELINA":	"MS,MT",
    "CANOLA	":	"CO,ID,IN,KS,KY,LA,MN,MO,MT,ND,OK,OR,PA,TN,TX,WA",
    "CARROTS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CAULIFLOWER":	"AL,AK,AZ,AR,CA,CO,CT,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "CELERY":	"AK,AZ,AR,CA,CO,CT,GA,HI,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MO,MT,NE,NH,NJ,NM,NY,NC,OH,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV",
    "CHERIMOYAS":	"CA,HI",
    "CHERRIES":	"AL,AK,AZ,AR,CA,CO,CT,FL,GA,HI,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CHESTNUTS":	"AL,AR,CA,CT,FL,GA,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MS,MO,NJ,NM,NY,NC,OH,OR,PA,RI,SC,TN,TX,VT,VA,WA,WV,WI",
    "CHICKPEAS":	"AZ,CA,ID,MN,MT,NE,ND,OR,SD,WA,WY",
    "CHICORY":	"CA,CT,IL,KY,LA,ME,MD,MA,MT,NJ,NY,NC,OR,PA,SC,VT,VA,WA,WI",
    "CITRUS TOTALS":	"AL,AZ,CA,FL,GA,HI,LA,SC,TX",
    "CITRUS, OTHER":	"CA,HI,TX",
    "COFFEE":	"HI",
    "CORN, GRAIN":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CORN, SILAGE":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CORN, TRADITIONAL OR INDIAN":	"AZ,CA,CO,CT,IL,IN,IA,KY,ME,MD,MA,MN,NJ,NM,NY,NC,OH,OR,PA,TN,UT,WA,WI",
    "COTTON":	"AL,AZ,AR,CA,FL,GA,KS,LA,MS,MO,NM,NC,OK,SC,TN,TX,VA",
    "CRANBERRIES":	"ME,MA,MI,NJ,OR,WA,WI",
    "CUCUMBERS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "CURRANTS":	"AK,CA,IL,IN,MD,MA,MI,MN,MT,NH,NJ,NY,ND,OH,OR,PA,SD,UT,VT,WA,WI",
    "DAIKON":	"AZ,CA,CO,CT,FL,GA,HI,IL,IN,IA,KS,LA,ME,MD,MA,MI,MN,MO,MT,NE,NH,NJ,NM,NY,NC,OH,OR,PA,SC,TN,TX,VT,VA,WA,WI",
    "DATES":	"AZ,CA,NM",
    "EGGPLANT":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "ELDERBERRIES":	"AL,CA,CO,CT,FL,GA,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,NE,NH,NJ,NY,NC,OH,OK,OR,PA,SC,SD,TN,TX,VT,VA,WA,WV,WI",
    "EMMER & SPELT":	"IL,IN,KY,ME,MD,MI,MO,MT,NY,ND,OH,PA,WA,WV,WI",
    "ESCAROLE & ENDIVE":	"CA,CO,CT,FL,GA,HI,IL,IN,IA,KY,ME,MD,MA,MI,MN,MO,MT,NH,NJ,NY,NC,OH,OR,PA,TN,VT,VA,WA,WI",
    "FIGS":	"AL,AR,CA,DE,FL,GA,IL,KY,LA,MD,MS,MO,NJ,NM,NY,NC,OK,OR,PA,SC,TN,TX,VA,WA,WV",
    "FLAXSEED":	"ID,MN,MT,ND,OR,SD,WA",
    "GARLIC":	"AL,AK,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,NE,NV,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TX,UT,VT,VA,WA,WV,WI,WY",
    "GINGER ROOT":	"AL,AZ,CA,CT,FL,GA,HI,ID,IL,IN,KS,KY,ME,MD,MA,MI,MN,MS,MO,NJ,NY,NC,OR,PA,SC,TN,VT,VA,WI",
    "GINSENG":	"CA,KY,NY,NC,SC,TN,WI",
    "GRAPEFRUIT":	"AL,AZ,CA,FL,HI,LA,TX",
    "GRAPES":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "GRASSES & LEGUMESTOTALS":	"CA,CO,FL,GA,ID,KS,KY,MN,MT,NE,NV,OR,UT,WA,WY",
    "GREENS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "GUAR":	"OK,TX",
    "GUAVAS":	"CA,FL,HI,TX",
    "HAY":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAY & HAYLAGE":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAY, (EXCL ALFALFA)":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAY, ALFALFA":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAY, IRRIGATED":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,WA,WI,WY",
    "HAYLAGE":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAYLAGE, ALFALFA":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "HAZELNUTS":	"AL,AR,CA,CO,CT,FL,GA,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,NE,NJ,NM,NY,NC,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "HERBS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SD,TN,TX,UT,VT,VA,WA,WI,WY",
    "HERBS, DRY":	"AK,CA,CO,CT,GA,HI,KY,ME,MA,MI,MT,NM,NY,NC,OR,PA,SD,TN,TX,VT,VA,WV",
    "HOPS":	"AR,CO,CT,ID,IL,IN,IA,KY,ME,MD,MA,MI,MN,MO,MT,NV,NJ,NM,NY,NC,OH,OR,PA,TN,VT,VA,WA,WI",
    "HORSERADISH":	"AL,AZ,CA,CO,CT,HI,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MO,NE,NH,NJ,NY,NC,OH,PA,SD,TN,VT,VA,WA,WV",
    "JOJOBA":	"AZ,CA",
    "KIWIFRUIT":	"AL,CA,FL,GA,MS,MO,NC,OR,PA,SC,TN,VT,VA,WA,WV",
    "KUMQUATS":	"CA,FL,HI,TX",
    "LEGUMES, ALFALFA,SEED":	"AZ,CA,ID,KS,MT,NE,OR,PA,SD,TX,UT,VA,WA,WY",
    "LEMONS":	"AZ,CA,FL,GA,HI,LA,MS,TX",
    "LENTILS":	"CA,ID,MN,MT,NE,NY,ND,SD,WA",
    "LETTUCE":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "LIMES":	"AL,AZ,CA,FL,GA,HI,LA,MS,TX",
    "LOGANBERRIES":	"CA,FL,MI,NC,OR,TN,WA",
    "MACADAMIAS":	"CA,FL,HI",
    "MANGOES":	"CA,FL,HI,TX",
    "MELONS":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "MINT, OIL":	"CA,ID,IN,OR,TN,WA,WV,WI",
    "MISCANTHUS":	"MO,NC",
    "MUSTARD, SEED":	"CA,ID,MT,NC,ND,OR,WA",
    "NECTARINES":	"AL,AZ,AR,CA,CO,CT,FL,GA,ID,IL,IN,KS,KY,ME,MD,MA,MI,MS,MO,NH,NJ,NM,NY,NC,OH,OK,OR,PA,SC,TN,TX,UT,WA,WV",
    "OATS":	"AL,AK,AR,CA,CO,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "OKRA":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,NE,NJ,NM,NY,NC,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "OLIVES":	"AZ,CA,GA,IL,OR,TX",
    "ONIONS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "ORANGES":	"AL,AZ,CA,FL,GA,HI,LA,MS,SC,TX",
    "ORCHARDS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "PAPAYAS":	"CA,FL,HI,TX",
    "PARSLEY":	"AL,AK,AR,CA,CO,CT,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MO,MT,NE,NV,NH,NJ,NM,NY,NC,OH,OR,PA,RI,SD,TN,UT,VT,VA,WA,WV,WI",
    "PASSION FRUIT":	"CA,FL,HI",
    "PEACHES":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "PEANUTS":	"AL,AR,CA,FL,GA,HI,LA,MS,NM,NC,OK,SC,TX,VA",
    "PEARS":	"AL,AZ,AR,CA,CO,CT,DE,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "PEAS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "PEAS, AUSTRIAN WINTER":	"CO,ID,MT,OR,WA",
    "PEAS, DRY EDIBLE":	"CA,CO,ID,IL,IA,KS,MI,MN,MO,MT,NE,NM,NY,ND,OK,OR,SC,SD,TX,WA,WI,WY",
    "PECANS":	"AL,AZ,AR,CA,FL,GA,IL,IN,KS,KY,LA,MD,MI,MS,MO,NE,NV,NM,NY,NC,OH,OK,SC,TN,TX,UT,VA",
    "PEPPERS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "PERSIMMONS":	"AL,AR,CA,CT,FL,GA,HI,IL,IN,IA,KS,KY,LA,MD,MI,MS,MO,NJ,NY,NC,OH,OK,OR,PA,SC,TN,TX,VA,WA,WV,WI",
    "PINEAPPLES":	"HI",
    "PISTACHIOS":	"AZ,CA,NV,NM,TX,UT",
    "PLUMS":	"AL,AZ,AR,CA,CO,CT,ID,IL,IN,IA,KY,LA,ME,MA,MI,MS,MO,MT,NE,NV,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WY",
    "POMEGRANATES":	"AL,AZ,CA,FL,GA,HI,LA,MS,NV,NM,SC,TX,UT",
    "POTATOES":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "PRUNES":	"CA,CO,ID,IL,ME,MA,MI,MO,MT,NM,NY,OH,OR,PA,TN,UT,WA",
    "PUMPKINS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "RADISHES":	"AL,AK,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "RAPESEED":	"ID,MI,NC,OR,PA,SC",
    "RASPBERRIES":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "RHUBARB":	"AL,AK,AR,CO,CT,GA,HI,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MS,MO,MT,NE,NJ,NM,NY,NC,OH,OR,PA,RI,SD,TN,UT,VT,VA,WA,WV,WI,WY",
    "RICE":	"AR,CA,FL,LA,MS,MO,TN,TX",
    "RYE":	"AL,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,ME,MD,MA,MI,MN,MO,MT,NE,NJ,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,VT,VA,WA,WV,WI",
    "SAFFLOWER":	"CA,ID,MT,ND,SD,UT",
    "SESAME":	"FL,KS,OK,TX",
    "SORGHUM, GRAIN":	"AL,AZ,AR,CA,CO,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,MD,MI,MN,MS,MO,MT,NE,NJ,NM,NY,NC,ND,OH,OK,PA,SC,SD,TN,TX,VA,WV,WI",
    "SORGHUM, SILAGE":	"AL,AZ,AR,CA,CO,FL,GA,ID,IL,IN,IA,KS,KY,LA,MD,MI,MN,MO,NE,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VA,WV,WI,WY",
    "SOYBEANS":	"AL,AR,CO,CT,DE,FL,GA,HI,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NJ,NM,NY,NC,ND,OH,OK,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "SPINACH":	"AL,AK,AZ,AR,CA,CO,DE,FL,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,OH,OK,OR,PA,RI,SC,SD,TX,UT,VT,VA,WA,WV,WI,WY",
    "SQUASH":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "STRAWBERRIES":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "SUGARBEETS":	"CO,ID,MI,MN,MT,NE,ND,OR,WY",
    "SUNFLOWER":	"AL,CA,CO,FL,GA,IL,IN,IA,KS,KY,MD,MI,MN,MO,MT,NE,NJ,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,VA,WA,WV,WI,WY",
    "SWEET CORN":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "SWEET POTATOES":	"AL,AZ,AR,CA,CO,CT,DE,FL,GA,HI,IL,IN,IA,KS,KY,LA,ME,MD,MA,MN,MS,MT,NE,NH,NJ,NM,NY,NC,ND,OH,OK,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI",
    "TANGELOS":	"AL,AZ,CA,FL,HI,TX",
    "TANGERINES":	"AL,AZ,CA,FL,GA,HI,LA,MS,TX",
    "TARO":	"CA,HI,ME,MA",
    "TOBACCO":	"CT,FL,GA,IN,KY,MD,MA,MO,NC,OH,PA,SC,TN,VA,WI",
    "TOMATOES":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,NE,NV,NH,NJ,NM,NY,NC,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "TRITICALE":	"CA,CO,ID,IL,IN,IA,KS,MD,MI,MN,MO,MT,NE,NY,NC,ND,OH,OK,OR,PA,SD,TN,TX,UT,VA,WA,WI,WY",
    "TURNIPS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,TN,TX,VT,VA,WA,WV,WI,WY",
    "VEGETABLE TOTALS":	"AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "WALNUTS":	"AL,AZ,AR,CA,CO,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,NE,NV,NJ,NM,NY,NC,OH,OK,OR,PA,RI,SC,TN,TX,UT,VT,VA,WA,WV,WI",
    "WATERCRESS":	"CA,CT,HI,IL,ME,MD,MA,MI,MN,MS,NY,NC,OH,OR,TN,VA,WA,WI",
    "WHEAT":	"AL,AK,AZ,AR,CA,CO,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MI,MN,MS,MO,MT,NE,NV,NJ,NM,NY,NC,ND,OH,OK,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "WHEAT, SPRING, DURUM":	"AZ,CA,CO,ID,MN,MT,NM,NY,ND,OR,SD",
    "WHEAT, WINTER":	"AL,AR,CA,CO,DE,FL,GA,ID,IL,IN,IA,KS,KY,LA,ME,MD,MI,MN,MS,MO,MT,NE,NJ,NM,NY,NC,ND,OH,OR,PA,SC,SD,TN,TX,UT,VT,VA,WA,WV,WY",
    "WILD RICE":	"CA,MN",
}
# fmt: on

LABEL_CONV_STATES = {
    "ALL": "AL,AK,AZ,AR,CA,CO,CT,DE,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,ND,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY",
    "EastofRockies": "MT,WY,CO,NM,ND,SD,NE,AR,CT,DE,FL,GA,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,NV,NH,NJ,NY,NC,OH,OK,PA,RI,SC,TN,TX,VT,VA,WV,WI",
    "WestofRockies": "WA,OR,CA,ID,NV,MT,WY,UT,CO,AZ,NM,AK,HI",
}

STATE_TO_HUC_LUT_LEGACY_ESA = {
    "AK": "19a,19b",
    "AL": "3,6",
    "AR": "8,11a",
    "AZ": "14,15a,15b",
    "CA": "17a,18a,18b",
    "CO": "10a,10b,11b,13,14",
    "CT": "1",
    "DC": "2",
    "DE": "2",
    "FL": "3",
    "GA": "3,6",
    "HI": "20a,20b",
    "IA": "7,10a",
    "ID": "17b",
    "IL": "5,7",
    "IN": "7,5,4",
    "KS": "10a,11a,11b",
    "KY": "5",
    "LA": "8,11a",
    "MA": "1",
    "MD": "2",
    "ME": "1",
    "MI": "4",
    "MN": "4,7,9",
    "MO": "7,10a,11a",
    "MS": "3,8",
    "MT": "10b,17b",
    "NC": "3,6",
    "ND": "9,10b",
    "NE": "10a",
    "NH": "1",
    "NJ": "2",
    "NM": "11b,12b,13,14,15a,15b",
    "NV": "15a,16a,16b",
    "NY": "2,4",
    "OH": "4,5",
    "OK": "11a,11b",
    "OR": "17a,17b",
    "PA": "2,5",
    "RI": "1",
    "SC": "3",
    "SD": "10a,10b",
    "TN": "5,6,8",
    "TX": "11a,11b,12a,12b,13",
    "UT": "14,15a,16a",
    "VA": "2,3,5,6",
    "VT": "1,4",
    "WA": "17a,17b",
    "WI": "4,7",
    "WV": "2,5",
    "WY": "10b,14,17b",
}

STATE_TO_HUC_LUT_NEW = {
    # "AK":
    "AL": "3W,6",
    "AR": "8,11",
    # "AS": "",
    "AZ": "14,15",
    "CA": "18",
    "CO": "10L,11,13,14",
    "CT": "1",
    # "DC": "",
    "DE": "2",
    "FL": "3S,3W",
    "GA": "3S,3W,3N,6",
    # "HI": "",
    "IA": "7,10L",
    "ID": "17",
    "IL": "5,7",
    "IN": "4,5",
    "KS": "10L,11",
    "KY": "5",
    "LA": "8,11",
    "MA": "1",
    "MD": "2",
    "ME": "1",
    "MI": "4",
    "MN": "7,9",
    "MO": "7,8,10L,11",
    "MS": "3W,8",
    "MT": "10U,17",
    "NC": "3N,6",
    "ND": "9,10U",
    "NE": "10L,10U",
    "NH": "1",
    "NJ": "2",
    "NM": "11,12,13,14,15",
    "NV": "15,16",
    "NY": "2,4",
    "OH": "4,5",
    "OK": "11",
    "OR": "17,18",
    "PA": "2,5",
    "RI": "1",
    "SC": "3N",
    "SD": "10U",
    "TN": "5,6,8",
    "TX": "11,12,13",
    "UT": "14,16",
    "VA": "2,3N,5,6",
    "VT": "1,2",
    "WA": "17",
    "WI": "4,7",
    "WV": "2,5",
    "WY": "10U,10L,17",
}


class PwcToolAlgoThread(qtc.QThread):
    """Class for the PWC tool algorithm thread"""

    update_diagnostics = qtc.pyqtSignal(str)
    update_progress = qtc.pyqtSignal(float)

    def __init__(self, settings: dict[str, Any]) -> None:
        super().__init__()

        self.settings = settings

        self._scenarios: dict[str, tuple[date, date]] = {}
        self._error_max_amt: list[str] = []
        self._error_scn_file_notexist: list[str] = []
        self.state_to_huc_lookup_table = pd.DataFrame.from_dict(
            data=STATE_TO_HUC_LUT, orient="index", columns=["HUC2s"]
        )
        self.crop_to_state_lookup_table = pd.DataFrame.from_dict(
            data=CROP_TO_STATE_LUT, orient="index", columns=["States"]
        )

    def run(self):
        """Manages PWC tool algorithm components.
        Run is a method of QThread which is automatically executed
        upon calling .start() method from the isntantiated worker.
        """
        self.update_diagnostics.emit("\nInitializing...")

        # debugpy.debug_this_thread()

        # create new batch file
        if self.settings["USE_CASE"] == "Use Case #1":
            logger.debug("Preparing to generate PWC batch file from scratch.")
            self.update_diagnostics.emit("Preparing to generate PWC batch file from scratch.")

            # read relavent tables
            ag_practices_table = self.read_ag_practices_table()
            drift_reduction_table = self.read_drift_reduction_table()
            ingredient_fate_params_table = self.read_ingredient_fate_parameters_table()
            bin_to_landsape_params_lookup_table = self.read_bin_to_landscape_lookup_table()

            if self.settings["WETMONTH_PRIORITIZATION"]:
                wettest_month_table = pd.read_csv(self.settings["FILE_PATHS"]["WETTEST_MONTH_CSV"], index_col="HUC2")
            else:
                wettest_month_table = None

            self.generate_batch_file_from_scratch(
                ag_practices_table,
                drift_reduction_table,
                wettest_month_table,
                ingredient_fate_params_table,
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

        Returns:
            pd.DataFrame: input pwc batch file
        """
        input_pwc_batch_file: pd.DataFrame = pd.read_csv(self.settings["FILE_PATHS"]["PWC_BATCH_CSV"])
        return input_pwc_batch_file

    def read_ag_practices_table(self) -> pd.DataFrame:
        """Reads the ag practices table.

        Returns:
            pd.DataFrame: ag practices table
        """

        ag_practices_excel_obj = pd.ExcelFile(
            self.settings["FILE_PATHS"]["AGRONOMIC_PRACTICES_EXCEL"], engine="openpyxl"
        )
        ag_practices_table: pd.DataFrame = pd.read_excel(
            ag_practices_excel_obj, sheet_name=self.settings["APT_SCENARIO"]
        )
        ag_practices_table.set_index(keys="RunDescriptor", inplace=True)

        return ag_practices_table

    def read_drift_reduction_table(self) -> pd.DataFrame:
        """Reads the drift reduction table.

        Returns:
            pd.DataFrame: drift reduction table
        """

        # read the drift reduction table
        drift_reduction_table: pd.DataFrame = pd.read_excel(
            self.settings["FILE_PATHS"]["AGDRIFT_REDUCTION_TABLE"],
            sheet_name=self.settings["DRT_SCENARIO"],
        )
        drift_reduction_table.set_index(keys="Profile", inplace=True)

        return drift_reduction_table

    def read_ingredient_fate_parameters_table(self) -> pd.DataFrame:
        """Reads the ingredient fate parameters table.

        Returns:
            pd.DataFrame: ingredient fate parameters table
        """

        ingred_fate_param_table = pd.read_csv(self.settings["FILE_PATHS"]["INGR_FATE_PARAMS"])

        return ingred_fate_param_table

    def read_bin_to_landscape_lookup_table(self) -> pd.DataFrame:
        """Reads the bin to landscape lookup table

        Returns:
            pd.DataFrame: bin to landscape lookup table
        """

        bin_to_landscape_lookup_table = pd.read_csv(self.settings["FILE_PATHS"]["BIN_TO_LANDSCAPE"], index_col="Bin")

        return bin_to_landscape_lookup_table

    #### QC BATCH FILE ####

    def quality_check_batch_file(
        self, input_pwc_batch_file: pd.DataFrame, ag_practices_table: pd.DataFrame, drift_reduction_table: pd.DataFrame
    ):
        """QCs the batch file. Does not update anything. Writes results/log file to output dir."""

        logger.info("Quality checking input PWC batch file...")
        self.update_diagnostics.emit("\nQuality checking input PWC batch file...")

        input_pwc_batch_file = standardize_field_names(input_pwc_batch_file)

        qc_results = qc_batch_file(
            input_pwc_batch_file, ag_practices_table.copy(deep=True), drift_reduction_table, self.settings
        )
        self.update_progress.emit(100)

        qc_results_output = pd.DataFrame.from_dict(data=qc_results, orient="columns")

        # create final pass/fail column, pass if everything is within label restrictions
        check_columns = [col for col in qc_results_output.columns if "Check" in col]
        qc_results_output.insert(loc=0, column="RunisValid", value=qc_results_output[check_columns].eq(True).all(1))
        try:
            qc_results_output.to_csv(
                os.path.join(self.settings["FILE_PATHS"]["OUTPUT_DIR"], f"{self.settings['RUN_ID']} QC Results.csv"),
                index=False,
            )
        except PermissionError:
            self.update_diagnostics.emit("\nError: A csv with the same name as the QC report is open.")
            self.update_diagnostics.emit("Please close it and rerun the PWC Tool.")
            self.update_progress.emit(0)
            return False

        logger.info("\nSuccess! Check the output directory for a full QC report.")
        self.update_diagnostics.emit("Success! Check the output directory for a full QC report.")

    ### GENERATE BATCH FILE FROM SCRATCH ####

    def generate_batch_file_from_scratch(
        self,
        ag_practices_table: pd.DataFrame,
        drift_reduction_table: pd.DataFrame,
        wettest_month_table: Union[pd.DataFrame, None],
        ingredient_fate_params_table: pd.DataFrame,
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
            bin_to_landsape_params_lookup_table (pd.DataFrame): bin to landscape params lookup table
        """

        start_time = time.time()  # start timer
        store_all_runs: list[dict[str, Any]] = []
        ingred_fate_params = dict(zip(ingredient_fate_params_table["Parameter"], ingredient_fate_params_table["Value"]))

        # convert lbs/acre to kg/ha for all rate fields
        ag_practices_table["MaxAnnAmt_lbsacre"] = ag_practices_table["MaxAnnAmt_lbsacre"] * 1.120851
        ag_practices_table["PostEmergence_MaxAmt_lbsacre"] = (
            ag_practices_table["PostEmergence_MaxAmt_lbsacre"] * 1.120851
        )
        ag_practices_table["PreEmergence_MaxAmt_lbsacre"] = ag_practices_table["PreEmergence_MaxAmt_lbsacre"] * 1.120851
        ag_practices_table["Rate1_MaxAppRate_lbsacre"] = ag_practices_table["Rate1_MaxAppRate_lbsacre"] * 1.120851
        ag_practices_table["Rate2_MaxAppRate_lbsacre"] = ag_practices_table["Rate2_MaxAppRate_lbsacre"] * 1.120851
        ag_practices_table["Rate3_MaxAppRate_lbsacre"] = ag_practices_table["Rate3_MaxAppRate_lbsacre"] * 1.120851
        ag_practices_table["Rate4_MaxAppRate_lbsacre"] = ag_practices_table["Rate4_MaxAppRate_lbsacre"] * 1.120851
        # use zero for PHI if not specified
        ag_practices_table["PHI"].fillna(value=0, inplace=True)

        # prepare for blank fields
        blank_fields = {}
        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            blank_fields[f"blank {i}"] = pd.NA

        # prepare for file naming
        if self.settings["RANDOM_START_DATES"]:
            start_dates = "rand-startdates"
        else:
            start_dates = "norand-startdates"

        if self.settings["DATE_PRIORITIZATION"] == "Wettest Month":
            date_prior = "pr-wetmonth"
        else:
            date_prior = "pr-maxrate"

        # prepare for progress updates
        total_rows_in_apt = len(ag_practices_table.index)
        ag_practices_table.reset_index(inplace=True)

        run_distances_all_methods: dict[int, list] = self.get_run_distances_for_each_app_method()

        bins_ = [bin_ for bin_, val in self.settings["BINS"].items() if val]

        # iterate through each row in the apt
        num_runs = 0
        for apt_indx, run_ag_pract in ag_practices_table.iterrows():
            if num_runs > 0:
                self.update_progress.emit((apt_indx / total_rows_in_apt) * 100)

            states: list[str] = lookup_states_from_crop(
                self.crop_to_state_lookup_table, run_ag_pract, LABEL_CONV_STATES
            )
            huc2s = lookup_huc_from_state(self.state_to_huc_lookup_table, states)
            application_method = run_ag_pract["ApplicationMethod"]
            drift_profile = get_drift_profile(run_ag_pract)
            run_distances = run_distances_all_methods[application_method]
            depths, tband = self.get_app_method_depths_and_tband(application_method)

            for huc2 in huc2s:
                run_names = []
                scenario_base = f"{run_ag_pract['Scenario']}{huc2}"
                scenario_full = f"{scenario_base}.scn"

                if not os.path.exists(os.path.join(self.settings["FILE_PATHS"]["SCENARIO_FILES_PATH"], scenario_full)):
                    self._error_scn_file_notexist.append(scenario_base)
                    logger.warning(f"\n {scenario_base} may not exist. Skipping huc {huc2}")
                    continue

                # get emergence and harvest date
                run_ag_pract["Emergence"], run_ag_pract["Harvest"] = self.get_scenario_dates(scenario_full)
                first_run_in_huc = True

                # report to log file
                logger.debug("\n------------------------------------------------------------------------------------")
                logger.debug("\nRun Descriptor: %s", run_ag_pract["RunDescriptor"])
                logger.debug("Application Method: %s", application_method)
                logger.debug("Valid states: %s", run_ag_pract["States"])
                logger.debug("HUC2: %s", huc2)
                logger.debug("Bins to process: %s", bins_)
                logger.debug("Distances to process: %s", run_distances)
                logger.debug("Date prioritization: %s", self.settings["DATE_PRIORITIZATION"])
                logger.debug("Random start dates: %s", self.settings["RANDOM_START_DATES"])
                if self.settings["RANDOM_START_DATES"]:
                    logger.debug("Random Seed: %s", self.settings["RANDOM_SEED"])

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

                    # derive special date istructions (dependent on emergence and harvest dates)
                    (
                        run_ag_pract[f"{rate}_instr_startdate"],
                        run_ag_pract[f"{rate}_instr_enddate"],
                        run_ag_pract[f"{rate}_instr_timeframe"],
                    ) = derive_instruction_date_restrictions(rate, run_ag_pract)

                for bin_ in bins_:
                    try:
                        landscape_params: dict[str, float] = (
                            bin_to_landsape_params_lookup_table.loc[int(bin_), :].copy(deep=True).to_dict()
                        )
                    except KeyError:
                        logger.warning(f"\n ERROR: bin {bin_} may not be in the bin to landscape params table.")
                        logger.warning(f" Skipping all bin {bin_} runs...")
                        continue

                    for distance in run_distances:
                        drift_profile_bin = f"{bin_}-{drift_profile}"
                        try:
                            drift_value = drift_reduction_table.at[drift_profile_bin, distance]
                            eff = drift_reduction_table.at[drift_profile_bin, "Efficiency"]
                        except KeyError:
                            logger.warning(f"\n ERROR: drift profile {drift_profile_bin} may not be in the DRT.")
                            logger.warning(f" Skipping all bin {drift_profile_bin} runs...")
                            continue

                        # RD, R, D
                        transport_mechanisms = self.get_transport_mechanisms(
                            application_method, drift_profile, distance
                        )
                        for transport_mech in transport_mechanisms:  # RD or R or D
                            if transport_mech == "D":  # change to drift only app method depth combo
                                application_method_used = 4
                                depths_used = [8]
                            else:
                                application_method_used = application_method
                                depths_used = depths

                            for depth in depths_used:
                                run_name = f"{run_ag_pract['RunDescriptor']}_huc{huc2}_{scenario_base}_bin{bin_}_appmeth{application_method_used}_{drift_profile}_{distance}_{transport_mech}_{depth}-depth_{tband}-tband_{start_dates}_{date_prior}"
                                run_names.append(run_name)

                                if first_run_in_huc:
                                    logger.debug("\nRun Ag. Practices:")
                                    logger.debug(run_ag_pract)
                                    if self.settings["WETMONTH_PRIORITIZATION"]:
                                        logger.debug("\nWettest Months:")
                                        logger.debug(wettest_month_table.loc[huc2, :].T)

                                run_storage: dict[str, Any] = {}  # new run (row) in batch file

                                run_storage["Run Descriptor"] = run_ag_pract["RunDescriptor"]

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

                                app_dates_rates = self.assign_application_dates(
                                    wettest_month_table, run_ag_pract.copy(deep=True), huc2, first_run_in_huc, run_name
                                )

                                run_storage["NumberofApplications"] = len(app_dates_rates)
                                run_storage["Absolute Dates?"] = "TRUE"
                                run_storage["Relative Dates?"] = pd.NA

                                for app_num, (app_date, app_rate) in enumerate(app_dates_rates):
                                    run_storage[f"Day{app_num+1}"] = app_date.day
                                    run_storage[f"Month{app_num+1}"] = app_date.month
                                    run_storage[f"AppRate (kg/ha){app_num+1}"] = app_rate
                                    run_storage[f"ApplicationMethod{app_num+1}"] = application_method_used
                                    if depth == "no":
                                        run_storage[f"Depth(cm){app_num+1}"] = ""
                                    else:
                                        run_storage[f"Depth(cm){app_num+1}"] = depth
                                    if tband == "no":
                                        run_storage[f"T-BandSplit{app_num+1}"] = ""
                                    else:
                                        run_storage[f"T-BandSplit{app_num+1}"] = tband
                                    run_storage[f"Eff.{app_num+1}"] = eff
                                    run_storage[f"Drift{app_num+1}"] = drift_value

                                store_all_runs.append(run_storage)  # store run values

                                first_run_in_huc = False
                                num_runs += 1

                logger.debug(f"\nRuns for {run_ag_pract['RunDescriptor']} in HUC {huc2}:\n")
                for run_name in run_names:
                    logger.debug(f"{run_name}")

        self.update_progress.emit(100)

        # write new batch file to output csv
        new_batch_file = pd.DataFrame(store_all_runs)
        new_batch_file.replace({"nodepth": "", "notband": ""}, inplace=True)
        try:
            new_batch_file.to_csv(
                os.path.join(
                    self.settings["FILE_PATHS"]["OUTPUT_DIR"], f"{self.settings['RUN_ID']}_new_batch_file.csv"
                ),
                index=False,
            )
        except PermissionError:
            self.update_diagnostics.emit("\nError: An excel file with the same name as the new batch file is open.")
            self.update_diagnostics.emit("Please close it and rerun the PWC Tool.")
            self.update_progress.emit(0)
            return False

        # report any errors
        if len(self._error_max_amt) > 0:
            logger.warning("\n WARNING: The maximum annual amount was not reached for the following runs:")
            logger.warning(set(self._error_max_amt))
            logger.warning("\n For these runs, please ensure the agronomic practices table (APT) is correct.")
            logger.warning(" If the APT is correct, and random dates is turned on, it may be")
            logger.warning(" that the random date selection is preventing all possible apps")
            logger.warning(" from being made. You can try again or turn random dates off.")

            self.update_diagnostics.emit("\n WARNING: The maximum annual amount was not reached for some runs.")
            self.update_diagnostics.emit(" Please check the log file for a full report.")

        if len(self._error_scn_file_notexist) > 0:
            logger.warning("\n WARNING: Scenario files may not exist for the following crop-huc pairs:")
            logger.warning(set(self._error_scn_file_notexist))
            logger.warning("\n In these cases, the runs associated with that crop-HUC2 pair were skipped.")

            self.update_diagnostics.emit("\n WARNING: Scenario files may not exist for some crop-huc pairs.")
            self.update_diagnostics.emit(" Please check the log file for a full report.")

        # report excecution time
        execution_time = str(round(time.time() - start_time, 1))
        logger.debug("\n%s runs generated", num_runs)
        logger.debug("Execution time (seconds): %s", execution_time)

        self.update_diagnostics.emit(f"\nSuccess! {num_runs} Runs generated in {execution_time} seconds.")
        self.update_diagnostics.emit(
            "Please check the output directory for the log file which contains a full processing report."
        )

    def get_app_method_depths_and_tband(self, application_method: int):
        """Gets the depths selected by the user for the application method"""

        if application_method in [1, 2]:
            depths = ["no"]
            tband = "no"

        else:
            depths = []

            if application_method == 5:
                for depth in [4, 6, 8, 10, 12]:
                    if self.settings[f"APPMETH{application_method}_DEPTHS"][depth]:
                        depths.append(depth)
                tband = float(self.settings["APPMETH5_TBANDFRAC"])

            else:
                for depth in [2, 4, 6, 8, 10, 12]:
                    if self.settings[f"APPMETH{application_method}_DEPTHS"][depth]:
                        depths.append(depth)
                tband = "no"

        return depths, tband

    def get_run_distances_for_each_app_method(self) -> dict[int, list]:
        """Gets the run distances selected by the user for each application method.

        Returns:
            dict[int,list]: run distances corresponding to each application method
        """

        run_distances: dict[int, list] = {}

        for app_method in ALL_APPMETHODS:
            run_distances[app_method] = []
            if app_method in BURIED_APPMETHODS:
                run_distances[app_method].append("000m")
            else:
                for distance in ALL_DISTANCES:
                    if self.settings[f"APPMETH{app_method}_DISTANCES"][distance]:
                        run_distances[app_method].append(distance)

        return run_distances

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

    def get_transport_mechanisms(self, application_method, drift_profile, distance):
        """Get the transport mechansism associated with the application method"""

        transport_mechanisms = []

        if drift_profile == "G-NODRIFT":
            transport_mechanisms.append("R")

        else:  # drift profile is either aerial, ground, or airblast
            if application_method == FOLIAR_APPMETHOD:
                if self.settings["APPMETH2_DRIFT_ONLY"][distance]:
                    transport_mechanisms.append("D")
                if self.settings["APPMETH2_DISTANCES"][distance]:
                    transport_mechanisms.append("RD")
            else:
                transport_mechanisms.append("RD")

        return transport_mechanisms

    def assign_application_dates(
        self,
        wettest_month_table: Union[pd.DataFrame, None],
        ag_practices: pd.Series,
        huc2: str,
        first_run_in_huc: bool,
        run_name: str,
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
            first_run_in_huc (bool): denotes if this is the first run in a huc
            run_name (str): run name
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

        potential_app_dates = self.get_all_potential_app_dates(wettest_month_table, huc2)

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

                if valid_app_rate:
                    app_rate = adjust_app_rate(app_rate, appdate_interval, ag_practices, count)

                # Make applications as long as all conditions are met
                while (
                    (valid_start_date)
                    and (valid_app_rate)
                    and (valid_next_date)
                    and (app_rate > 0)
                    and (count.at[rate_id, "num_apps"] + 1 <= ag_practices[f"{rate_id}_MaxNumApps"])
                    and (count.at["Total", "num_apps"] + 1 <= ag_practices["MaxAnnNumApps"])
                    and (count.at["Total", "amt_applied"] + app_rate <= ag_practices["MaxAnnAmt_lbsacre"])
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
        if first_run_in_huc:
            logger.debug("\nApplications:")
            for app_date, rate in applications:
                logger.debug(f"   {app_date:%m-%d} @ {rate:0.2f} kg/ha ({rate/1.120851:0.2f} lb/ac)")

            # prepare count table for logging
            count["num_apps"] = count["num_apps"].astype(int)
            count["amt_applied_lbac"] = count["amt_applied"].copy(deep=True) / 1.120851
            count["amt_applied"] = count["amt_applied"].round(4)
            count["amt_applied_lbac"] = count["amt_applied_lbac"].round(4)
            count.rename(
                mapper={
                    "num_apps": "Num. Apps.",
                    "amt_applied": "Amt. Applied (kg/ha)",
                    "amt_applied_lbac": "Amt. Applied (lb/ac)",
                },
                axis=1,
                inplace=True,
            )
            logger.debug(f"\nFinal Totals:\n{count}")

            if count.at["Total", "Amt. Applied (kg/ha)"] + 0.01 < ag_practices["MaxAnnAmt_lbsacre"]:
                logger.warning(
                    f"\n WARNING: Annual maximum application amount of {ag_practices['MaxAnnAmt_lbsacre']} kg AI/ha not applied."
                )
                logger.warning(" Please ensure the agronomic practices table (APT) is correct.")
                logger.warning(" If the APT is correct, and random dates is turned on, it may be")
                logger.warning(" that the random date selection is preventing all possible apps")
                logger.warning(" from being made. You can try again or turn random dates off.")

                self._error_max_amt.append(run_name)

        return applications

    def get_all_potential_app_dates(self, wettest_month_table: Union[pd.DataFrame, None], huc2: str) -> list:
        """Gets all the potential application dates for the entire year. Returns a
        list of dates sorted in sequential order or according to wettest months.

        Args:
            wettest_month_table (pd.DataFrame): wettest months table
            huc2 (str): huc2 id
        Returns:
            list: potential app dates
        """

        # map months to number of days in the month
        days_in_month: dict = {}
        for month in range(1, 13):
            _, days_in_month[month] = calendar.monthrange(2021, month)

        potential_app_dates = []

        if self.settings["WETMONTH_PRIORITIZATION"]:
            months = wettest_month_table.loc[huc2, :].values.tolist()
        else:
            months = [month for month in range(1, 13)]

        for month in months:
            num_days_in_month = days_in_month[month]

            for day in range(1, num_days_in_month + 1):
                potential_app_dates.append(date(year=2021, month=month, day=day))

        return potential_app_dates

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
