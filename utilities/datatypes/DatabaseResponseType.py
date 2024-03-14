from enum import Enum


class DatabaseResponseType(Enum):
    NONE = 0
    MESSAGE = 1
    WARNING = 2
    ERROR = 3
