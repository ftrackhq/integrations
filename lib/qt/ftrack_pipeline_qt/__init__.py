from ._version import __version__

from ftrack_connect_pipeline.configure_logging import configure_logging

# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
from ftrack_connect_pipeline_qt.ui import (
    resource,
)
from ftrack_connect_pipeline_qt.ui import theme


configure_logging(__name__, extra_modules=['ftrack_connect_pipeline'])
