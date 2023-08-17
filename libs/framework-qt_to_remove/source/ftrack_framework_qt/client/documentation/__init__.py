# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import os.path
import subprocess
import platform

from Qt import QtWidgets


class QtDocumentationClientWidget(QtWidgets.QWidget):
    '''Client for opening Connect documentation URL'''

    documentation_url = None
    # The URL to documentation, if available. Should be set by DCC

    documentation_path = None
    # The path to local user documentation, if available. Should be set by DCC

    def __init__(self, event_manager, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    @staticmethod
    def _get_user_documentation_path(source_path, dcc_name):
        '''Calculcate the path to the user documentation based on *source_path*.
        Expect source path to be on the form:

        /Users/henriknorin/Library/Application Support/ftrack-connect-plugins/ftrack-connect-pipeline-nuke-1.1.0/
            dependencies/ftrack_connect_pipeline_nuke'''

        plugin_path = os.path.dirname(os.path.dirname(source_path))

        return os.path.join(
            plugin_path,
            'resource',
            'doc',
            '{} user documentation.pdf'.format(dcc_name.title()),
        )

    def _get_open_command(self, target):
        '''Generate operating system specific command to open *target*'''
        is_link = target.startswith('http')
        if platform.system() == "Windows":
            # Windows / PC
            if is_link:
                return ['CMD', '/C', 'START {}'.format(target)]
            else:
                return [target]
        elif platform.system() == "Darwin":
            # Mac OS
            if is_link:
                return ['open', target]
            else:
                return ['open "{}"'.format(target)]
        else:
            # Assume we are on linux
            if is_link:
                return ['xdg-open', target]
            else:
                return ['xdg-open "{}"'.format(target)]

    def show(self):
        '''Open the documentation in a browser or PDF viewer'''
        commands = None
        if self.documentation_path:
            if not os.path.exists(self.documentation_path):
                self.logger.error(
                    'User documentation path does not exist: {}'.format(
                        self.documentation_path
                    )
                )
                return
            commands = self._get_open_command(self.documentation_path)
            self.logger.debug(
                'Launching local user documentation through system command: {}'.format(
                    commands
                )
            )
            subprocess.Popen(commands, shell=True)
        else:
            # Fall back on Connect online documentation
            documentation_url_effective = (
                self.documentation_url
                or 'https://www.ftrack.com/en/portfolio/connect'
            )
            commands = self._get_open_command(documentation_url_effective)
            self.logger.debug(
                'Launching online documentation through system command: {}'.format(
                    commands
                )
            )
            subprocess.Popen(commands)
