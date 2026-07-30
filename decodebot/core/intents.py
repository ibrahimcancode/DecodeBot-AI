from enum import Enum, auto


class Intent(Enum):
    GREETING = auto()
    EXIT = auto()
    HELP = auto()
    ABOUT = auto()
    VERSION = auto()
    HISTORY = auto()
    STATS = auto()
    SETTINGS = auto()
    RESET = auto()
    CLEAR = auto()
    EASTER_EGG = auto()
    UNKNOWN = auto()
    EMPTY_INPUT = auto()
    NUMERIC_INPUT = auto()
    SYMBOLS_ONLY = auto()
