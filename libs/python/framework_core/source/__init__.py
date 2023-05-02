# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ._version import __version__

from framework_core import constants
from framework_core.configure_logging import configure_logging

configure_logging(__name__)
from framework_core.constants.asset import *
