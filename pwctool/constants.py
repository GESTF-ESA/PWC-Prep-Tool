"""Constants for the pwctool package."""

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
