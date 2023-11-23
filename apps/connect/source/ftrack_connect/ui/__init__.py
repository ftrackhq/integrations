# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# Import QtSvg and QtXml to force load libraries needed to display
# SVG on Windows.
from ftrack_connect.qt import QtSvg
from ftrack_connect.qt import QtXml


# Load UI resources such as icons.
from . import resource as _resource
