from ._version import __version__

from framework_core.configure_logging import configure_logging

# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
from framework_qt.ui import (
    resource,
)
from framework_qt.ui import theme


configure_logging(__name__, extra_modules=['framework_core'])
