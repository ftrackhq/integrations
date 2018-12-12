#! /usr/bin/env python

import os
import sys
from ftrack_connect_framework.ui import qt
from QtExt import QtGui


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = qt.main.QtFrameworkWidget()
    wid.show()
    sys.exit(app.exec_())
