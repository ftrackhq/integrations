# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import sys
import os
import signal

logger = logging.getLogger(__name__)


def terminate_current_process():
    '''Terminate integration process'''
    logger.warning('Terminating current process')

    if sys.platform == 'win32':
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        os.kill(os.getpid(), signal.SIGKILL)


class MonitorProcess(object):
    '''Assist monitor a process by its PID'''

    @property
    def process_pid(self):
        '''Return process PID.'''
        return self._process_pid

    @process_pid.setter
    def process_pid(self, value):
        '''Set process PID to *value*.'''
        if self._process_pid != value:
            self._process_pid = value
            logger.info(f'Process detected: {self.process_pid}')

    def __init__(self, probe_pid_callback):
        '''Monitor process probing pid through *probe_pid_callback*.'''
        self._probe_pid_callback = probe_pid_callback
        self._process_pid = None

    def _check_still_running(self):
        logger.info(
            f'Checking if application is still alive (pid: {self.process_pid})...'
        )
        pid = self._probe_pid_callback()
        is_same_process = pid == self.process_pid

        if pid is None:
            logger.info('Process no longer running.')

        elif not is_same_process:
            logger.info(
                f'Process pid changed from: {self.process_pid} to {pid}'
            )

        return is_same_process

    def check_running(self):
        '''Check if PID is running'''
        if self.process_pid:
            return self._check_still_running()

        self.process_pid = self._probe_pid_callback()
        if self.process_pid:
            return True

        logger.warning('Process not yet detected. Probing...')
        return False
