# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import subprocess
import platform

from Qt import QtWidgets


class QtDocumentationClientWidget(QtWidgets.QWidget):
    '''Client for opening Connect documentation URL'''

    def __init__(self, event_manager, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def show(self):
        '''Open the URL in operating system'''
        DOC_URL = 'https://www.ftrack.com/en/portfolio/connect'
        if platform.system() == "Windows":
            # Windows / PC
            commands = ['CMD', '/C', 'START {}'.format(DOC_URL)]
        elif platform.system() == "Darwin":
            # Mac OS
            commands = ['open', DOC_URL]
        else:
            # Assume we are on linux
            commands = ['xdg-open', DOC_URL]
        self.logger.debug(
            'Launching documentation through system command: {}'.format(
                commands
            )
        )
        subprocess.Popen(commands)
