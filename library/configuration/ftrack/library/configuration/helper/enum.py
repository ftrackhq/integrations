from enum import Enum


class METADATA(Enum):
    ROOT = "_metadata"
    SOURCES = "sources"
    DELETE = "delete-after-compose"
    CONFLICTS = "conflicts"


class CONFLICT_RESOLUTION(Enum):
    IGNORE = "ignore"
    WARN = "warn"
    FAIL = "fail"
    EXPLICIT = "explicit"
    ORDER = "order"
