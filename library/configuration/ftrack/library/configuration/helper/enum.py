from enum import Enum


class METADATA(Enum):
    ROOT = "_metadata"
    SOURCES = "sources"
    DELETE = "marked_for_deletion"
    CONFLICTS = "conflicts"


class CONFLICT_HANDLING(Enum):
    WARN = "warn"
    RAISE = "raise"
