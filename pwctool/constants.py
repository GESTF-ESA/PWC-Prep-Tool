"""Constants for the pwctool package."""

import pandas as pd

VERSION = "1.0.101"

# default directory for file explorer browsing
DEFAULT_DIR = "C:"

# list of aquatic bins - 4=static, 7=flowing, 10=wetland
ALL_BINS = [4, 7, 10]

# list of distances for drift and runoff calculations
ALL_DISTANCES: list[str] = ["000m", "030m", "060m", "090m", "120m", "150m"]

# list of depths for application methods that use depth
ALL_DEPTHS: list[int] = [2, 4, 6, 8, 10, 12]

# list of application methods
ALL_APPMETHODS: list[int] = [1, 2, 3, 4, 5, 6, 7]

# list of buried application methods
BURIED_APPMETHODS: list[int] = [3, 4, 5, 6, 7]

FOLIAR_APPMETHOD: int = 2

TBAND_APPMETHOD: int = 5

WATERBODY_PARAMS = pd.DataFrame(
    data={
        "FlowAvgTime": [1, 0, 1],
        "Field Size (m2)": [1730000, 100000, 100000],
        "Waterbody Area (m2)": [52600, 10000, 10000],
        "Init Depth (m)": [2.74, 2, 0.15],
        "Max Depth (m)": [2.74, 2, 0.15],
        "HL (m)": [600, 357, 357],
        "PUA": [1, 1, 1],
        "Baseflow": [0, 0, 0],
    },
    index=[4, 7, 10],
)
