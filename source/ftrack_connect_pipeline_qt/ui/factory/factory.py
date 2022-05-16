# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import logging
from functools import partial
import uuid
import json

from Qt import QtCore, QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.factory import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.factory import (
    overrides as override_widgets,
    default as default_widgets,
)
from ftrack_connect_pipeline_qt.ui.factory.client_ui_overrides import (
    UI_OVERRIDES,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt import constants as qt_constants
