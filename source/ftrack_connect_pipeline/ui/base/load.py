import logging
import ftrack_api
import os
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui import base

logger = logging.getLogger(__name__)


class BaseLoadUiFramework(base.BaseUiFramework):

    def __init__(self, *args, **kwargs):
        super(BaseLoadUiFramework, self).__init__()

        self.mapping = {}

