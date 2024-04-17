# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import sys
import subprocess
import re
import os
import signal

logger = logging.getLogger(__name__)


def probe_premiere_pid(premiere_version):
    if sys.platform == 'darwin':
        PS_EXECUTABLE = f'Adobe Premiere Pro {str(premiere_version)}'
        logger.info(f'Probing Mac PID (executable: {PS_EXECUTABLE})')

        for line in (
            subprocess.check_output(['ps', '-ef']).decode('utf-8').split('\n')
        ):
            if line.find(f'MacOS/{PS_EXECUTABLE}') > -1:
                # Expect:
                #   501 21270     1   0  3:05PM ??         0:36.85 /Applications/Adobe Premiere Pro 2024/Adobe Premiere Pro 2024.app/Contents/MacOS/Adobe Premiere Pro 2024
                pid = int(re.split(' +', line)[2])
                logger.info(f'Found pid: {pid}.')
                return pid

    elif sys.platform == 'win32':
        PS_EXECUTABLE = 'Premiere.exe'
        logger.info(f'Probing Windows PID (executable: {PS_EXECUTABLE}).')

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        for line in (
            subprocess.check_output(['TASKLIST'], startupinfo=startupinfo)
            .decode('cp850')
            .split('\n')
        ):
            if line.find(PS_EXECUTABLE) > -1:
                # Expect:
                #   Premiere.exe                15364 Console                    1  2 156 928 K
                pid = int(re.split(' +', line)[1])
                logger.info(f'Found pid: {pid}.')
                return pid

    logger.warning('Premiere not found running!')
    return None


def terminate_current_process():
    '''Terminate Premiere standalone integration process'''
    logger.warning('Terminating Premiere standalone framework integration')

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
            logger.info(f'Premiere process detected: {self.process_pid}')

    def __init__(self, premiere_version):
        '''Monitor premiere process of version *premiere_version*.'''
        self.premiere_version = premiere_version
        self._process_pid = None

    def _check_still_running(self):
        logger.info(
            f'Checking if PS is still alive (pid: {self.process_pid})...'
        )
        pid = probe_premiere_pid(self.premiere_version)
        is_same_process = pid == self.process_pid

        if pid is None:
            logger.info('Premiere no longer running.')

        elif not is_same_process:
            logger.info(
                f'Premiere process pid changed from: {self.process_pid} to {pid}'
            )

        return is_same_process

    def check_running(self):
        '''Check if PID is running'''
        if self.process_pid:
            return self._check_still_running()

        self.process_pid = probe_premiere_pid(self.premiere_version)
        if self.process_pid:
            return True

        logger.warning('Premiere process not yet detected. Probing...')
        return False
