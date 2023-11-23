# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import traceback
import sys
import subprocess
import re
import os
import signal

from ftrack_utils.framework.remote import get_integration_session_id

logger = logging.getLogger(__name__)


class BasePhotoshopRemoteConnection(object):
    '''Base Photoshop remote connection.'''

    @property
    def photoshop_version(self):
        '''Return Photoshop version.'''
        return self._photoshop_version

    @property
    def client(self):
        return self._client

    @property
    def event_manager(self):
        '''Return event manager.'''
        return self.client.event_manager

    @property
    def session(self):
        '''Return session.'''
        return self.event_manager.session

    @property
    def photoshop_version(self):
        '''Return Photoshop version.'''
        return self._photoshop_version

    @property
    def photoshop_pid(self):
        '''Return Photoshop PID.'''
        return self._photoshop_pid

    @property
    def connected(self):
        '''Return True if connected to Photoshop.'''
        return self._connected

    @connected.setter
    def connected(self, value):
        '''Set connected state to *value*.'''
        self._connected = value
        if self.connect:
            logger.info(
                'Successfully established connection to Photoshop {}'.format(
                    self.photoshop_version
                )
            )

    def __init__(self, client, photoshop_version, panel_launchers):
        super(BasePhotoshopRemoteConnection, self).__init__()

        assert (
            get_integration_session_id()
        ), 'Photoshop integration requires a FTRACK_INTEGRATION_SESSION_ID passed as environment variable!'

        self._client = client
        self._photoshop_version = photoshop_version
        self._panel_launchers = panel_launchers
        self._photoshop_pid = -1
        self._connected = False

        self._initialise()

    def _initialise(self):
        '''Initialise the Photoshop connection'''

        self.event_manager.subscribe.discover_remote_integration(
            get_integration_session_id(),
            self._on_discover_remote_integration_callback,
        )

    def _on_discover_remote_integration_callback(self, event):
        '''Callback for discover_remote_integration *event*, sends
        back context data'''
        if not self.connected:
            self.connected = True
            logger.info("Connected to Photoshop.")
        # Send acknowledgment back with launchers and current context data
        context_id = self.client.context_id
        task = self.session.query('Task where id={}'.format(context_id)).one()
        self.event_manager.publish.remote_integration_context_data(
            get_integration_session_id(),
            context_id,
            task['name'],
            task['type']['name'],
            ' / '.join([d["name"] for d in task["link"][:-1]]),
            task['thumbnail_url']['url'],
            task['project_id'],
            self._panel_launchers,
        )

    def probe_photoshop_pid(self):
        '''List processes using 'ps' to find photoshop pid'''
        PS_EXECUTABLE = "Adobe Photoshop {}".format(
            str(self._photoshop_version)
        )

        logger.info('Probing PID (executable: {}).'.format(PS_EXECUTABLE))

        if sys.platform == 'darwin':
            for line in (
                subprocess.check_output(["ps", "-ef"])
                .decode('utf-8')
                .split("\n")
            ):
                if line.find('MacOS/{}'.format(PS_EXECUTABLE)) > -1:
                    # Expect:
                    #   501 21270     1   0  3:05PM ??         0:36.85 /Applications/Adobe Photoshop 2022/Adobe Photoshop 2022.app/Contents/MacOS/Adobe Photoshop 2022
                    pid = int(re.split(" +", line)[2])
                    logger.info('Got Photoshop PID: {}'.format(pid))

                    if self._photoshop_pid == -1:
                        self._photoshop_pid = pid

                    return pid
        if self._photoshop_pid is None:
            raise Exception('Photoshop not found running!')
        else:
            logger.warning('Photoshop not found running!')

        return -1

    def connect(self):
        '''Connect with DCC over remote event hub, needs to be implemented by
        subclass'''
        raise NotImplemented()

    def check_responding(self):
        '''Check if Photoshop is alive, send ping'''
        logger.info(
            "Checking if PS (pid: {}) is still alive...".format(
                self._photoshop_pid
            )
        )
        try:
            # Send event and wait for reply sync
            event = self.event_manager.publish.discover_remote_integration(
                get_integration_session_id(),
                fetch_reply=True,
            )
            logger.info(
                'Got reply for integration discovery response event: {}'.format(
                    event
                )
            )
            return True
        except:
            logger.warning(traceback.format_exc())
            return False
        return True

    def check_running(self):
        '''Check if PID is running'''
        logger.info(
            "Checking if PS is still alive (pid: {})...".format(
                self._photoshop_pid
            )
        )

        pid = self.probe_photoshop_pid()
        return pid == self._photoshop_pid

    def terminate(self):
        '''Terminate Photoshop standalone integration process'''
        logger.info("Terminating Photoshop standalone framework integration")

        os.kill(os.getpid(), signal.SIGKILL)
