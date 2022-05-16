# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import subprocess
import platform

from ftrack_connect_pipeline.client import Client


class QtDocumentationClient(Client):
    '''Client for opening Connect documentation'''

    def __init__(self, event_manager, unused_asset_list_model):
        super(QtDocumentationClient, self).__init__(event_manager)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def show(self):
        DOC_URL = 'https://www.ftrack.com/en/portfolio/connect'
        if platform.system() == "Windows":
            commands = ['start']
        elif platform.system() == "Darwin":
            commands = ['open']
        else:
            # Assume linux
            commands = ['xdg-open']
        commands.append(DOC_URL)
        self.logger.debug(
            'Launching documentation through system command: {}'.format(
                commands
            )
        )
        subprocess.Popen(commands)
