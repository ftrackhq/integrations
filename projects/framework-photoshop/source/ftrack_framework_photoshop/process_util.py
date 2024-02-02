# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import sys
import subprocess
import re
import os
import signal

logger = logging.getLogger(__name__)


def probe_photoshop_pid(photoshop_version):
    if sys.platform == 'darwin':
        PS_EXECUTABLE = f'Adobe Photoshop {str(photoshop_version)}'
        logger.info(f'Probing Mac PID (executable: {PS_EXECUTABLE})')

        for line in (
            subprocess.check_output(['ps', '-ef']).decode('utf-8').split('\n')
        ):
            if line.find(f'MacOS/{PS_EXECUTABLE}') > -1:
                # Expect:
                #   501 21270     1   0  3:05PM ??         0:36.85 /Applications/Adobe Photoshop 2022/Adobe Photoshop 2022.app/Contents/MacOS/Adobe Photoshop 2022
                pid = int(re.split(' +', line)[2])
                logger.info(f'Found pid: {pid}.')
                return pid

    elif sys.platform == 'win32':
        PS_EXECUTABLE = 'Photoshop.exe'
        logger.info(f'Probing Windows PID (executable: {PS_EXECUTABLE}).')

        for line in (
            subprocess.check_output(['TASKLIST']).decode('cp850').split('\n')
        ):
            if line.find(PS_EXECUTABLE) > -1:
                # Expect:
                #   Photoshop.exe                15364 Console                    1  2 156 928 K
                pid = int(re.split(' +', line)[1])
                logger.info(f'Found pid: {pid}.')
                return pid

    logger.warning('Photoshop not found running!')
    return None


def terminate_current_process():
    '''Terminate Photoshop standalone integration process'''
    logger.warning('Terminating Photoshop standalone framework integration')

    if sys.platform == 'win32':
        os.kill(os.getpid(), signal.SIGTERM)
    else:
        os.kill(os.getpid(), signal.SIGKILL)


class MonitorProcess(object):
    @property
    def process_pid(self):
        '''Return process PID.'''
        return self._process_pid

    @process_pid.setter
    def process_pid(self, value):
        '''Set process PID to *value*.'''
        if self._process_pid != value:
            self._process_pid = value
            logger.info(f'Photoshop process detected: {self.process_pid}')

    def __init__(self, photoshop_version):
        '''Monitor photoshop process of version *photoshop_version*.'''
        self.photoshop_version = photoshop_version
        self._process_pid = None

    def _check_still_running(self):
        logger.info(
            f'Checking if PS is still alive (pid: {self.process_pid})...'
        )
        pid = probe_photoshop_pid(self.photoshop_version)
        is_same_process = pid == self.process_pid

        if pid is None:
            logger.info('Photoshop no longer running.')

        elif not is_same_process:
            logger.info(
                f'Photoshop process pid changed from: {self.process_pid} to {pid}'
            )

        return is_same_process

    def check_running(self):
        '''Check if PID is running'''
        if self.process_pid:
            return self._check_still_running()

        self.process_pid = probe_photoshop_pid(self.photoshop_version)
        if self.process_pid:
            return True

        logger.warning('Photoshop process not yet detected. Probing...')
        return False
