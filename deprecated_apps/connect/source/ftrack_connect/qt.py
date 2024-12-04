# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import (
        QtWidgets,
        QtCore,
        QtGui,
        QtNetwork,
        QtMultimedia,
        QtSvg,
        QtOpenGL,
        QtQuick,
    )
except ImportError:
    from PySide2 import (
        QtWidgets,
        QtCore,
        QtGui,
        QtNetwork,
        QtMultimedia,
        QtSvg,
        QtOpenGL,
        QtQuick,
    )
