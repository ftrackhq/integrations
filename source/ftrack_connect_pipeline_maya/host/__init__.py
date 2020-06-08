
import logging
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline.host import Host

logger = logging.getLogger(
    __name__
)

class MayaHost(Host):
    host = [qt_constants.HOST, maya_constants.HOST]