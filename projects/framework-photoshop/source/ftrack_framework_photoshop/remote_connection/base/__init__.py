# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import traceback
import sys
import subprocess
import re
import os
import signal

from ftrack_constants import framework as constants

logger = logging.getLogger(__name__)


class BasePhotoshopRemoteConnection(object):
    '''Base Photoshop remote connection.'''

    @property
    def integration_session_id(self):
        '''Return integration session id.'''
        return self._integration_session_id

    @property
    def photoshop_version(self):
        '''Return Photoshop version.'''
        return self._photoshop_version

    @property
    def event_manager(self):
        '''Return event manager.'''
        return self._event_manager

    @property
    def session(self):
        '''Return session.'''
        return self.event_manager.session

    @property
    def remote_event_manager(self):
        '''Return remote event manager, to plugins and other parts of the framework that
        needs to send events to Photoshop.'''
        return self._remote_event_manager

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

    def __init__(self, event_manager):
        super(BasePhotoshopRemoteConnection, self).__init__()

        self._integration_session_id = os.environ.get(
            'FTRACK_INTEGRATION_SESSION_ID'
        )
        assert (
            self._integration_session_id
        ), 'Photoshop integration requires a FTRACK_INTEGRATION_SESSION_ID passed as environment variable!'

        photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
        assert (
            photoshop_version
        ), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

        self._photoshop_version = int(photoshop_version)

        self._event_manager = event_manager
        self._photoshop_pid = -1
        self._connected = False
        self._remote_subscriber_id = None
        self._event_replies = {}

        self._initialise()

    def _initialise(self):
        '''Initialise the Photoshop connection'''

        self.event_manager.subscribe.remote_alive(
            self.integration_session_id, self._on_remote_alive_callback
        )

    # Event handling

    def _on_remote_alive_callback(self, event):
        # DEBUG, to be removed
        eid = event['id']
        topic = event['topic']
        event_data = event['data']
        source = event.get('source')
        logger.info(
            'Processing incoming PS event: {} ({}), data: {}, source: {}'.format(
                topic, eid, event_data, source
            )
        )

        self.connected = True
        # Send acknowledgment back with current context data
        context_id = os.getenv('FTRACK_CONTEXTID')
        task = self.session.query('Task where id={}'.format(context_id)).one()
        self.event_manager.publish.remote_context_data(
            self.integration_session_id,
            {
                'context_id': context_id,
                'context_name': task['name'],
                'context_type': task['type']['name'],
                'context_path': " / ".join(
                    [d["name"] for d in task["link"][:-1]]
                ),
                'context_thumbnail': task['thumbnail_url']['url'],
                'project_id': task['project_id'],
            },
        )

    def _on_remote_alive_ack_callback(self, event):
        logger.info('Got reply for integration alive event: {}'.format(event))

    # PID

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
            self.event_manager.publish.remote_alive(
                self.integration_session_id,
                callback=self._on_remote_alive_ack_callback,
            )
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
        if self._remote_subscriber_id:
            try:
                self.remote_event_manager.session.event_hub.unsubscribe(
                    self._remote_subscriber_id
                )
            except:
                logger.warning(traceback.format_exc())

        os.kill(os.getpid(), signal.SIGKILL)
