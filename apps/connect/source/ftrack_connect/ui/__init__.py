# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

# Import QtSvg and QtXml to force load libraries needed to display
# SVG on Windows.
try:
    from PySide6 import QtSvg, QtXml
except ImportError:
    from PySide2 import QtSvg, QtXml


# Load UI resources such as icons.
from . import resource as _resource
