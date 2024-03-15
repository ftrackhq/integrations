# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import sys
import qtawesome as qta

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import ftrack_api

import ftrack_connect.ui.application
import ftrack_connect.ui.widget.overlay
import ftrack_connect.ui.widget.item_list
import ftrack_connect.ui.widget.label
import ftrack_connect.ui.widget.line_edit
from ftrack_connect.util import get_connect_plugin_version

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.abspath(
    os.path.join(connect_plugin_path, 'dependencies')
)
sys.path.append(python_dependencies)

from ftrack_connect_timetracker_widget.timetracker import *

logger = logging.getLogger('ftrack_connect.plugin.timetracker_widget')

import ftrack_connect.error


class TimeTracker(ftrack_connect.ui.application.ConnectWidget):
    '''Base widget for ftrack connect time tracker plugin.'''

    @property
    def user(self):
        return self.session.query(
            'User where username is "{}"'.format(self.session.api_user)
        ).first()

    def __init__(self, *args, **kwargs):
        '''Instantiate the time tracker.'''
        super(TimeTracker, self).__init__(*args, **kwargs)
        self.setObjectName('timeTracker')

        self._activeEntity = None
        self._timelog = None
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.activeLabel = QtWidgets.QLabel('Currently running')
        self.activeLabel.setProperty('title', True)
        layout.addWidget(self.activeLabel)

        self._timerEnabled = False
        self.timer = Timer()
        layout.addWidget(self.timer)

        layout.addWidget(self.scroll_area)

        self.timer_place_holder = TimerOverlay(self.timer)

        # TODO: Add theme support.
        reloadIcon = qta.icon('mdi6.reload', color='#FFDD86', scale_factor=1)
        assignedTimeLogUpdateButton = QtWidgets.QPushButton(reloadIcon, '')
        assignedTimeLogUpdateButton.setFlat(True)
        assignedTimeLogUpdateButton.setToolTip('Refresh list')
        assignedTimeLogUpdateButton.clicked.connect(self._updateAssignedList)

        self.assignedTimeLogList = TimeLogList(
            title='Assigned', headerWidgets=[assignedTimeLogUpdateButton]
        )
        self.scroll_area.setWidget(self.assignedTimeLogList)
        self.timer.started.connect(self.startTime)

        # Connect events.
        self.timer.stopped.connect(self._onCommitTime)
        self.timer.timeEdited.connect(self._onCommitTime)

        self.assignedTimeLogList.itemSelected.connect(self._onSelectTimeLog)

        self._updateAssignedList()

    def _updateAssignedList(self):
        '''Update assigned list.'''
        self.assignedTimeLogList.clearItems()

        assigned_tasks = self.session.query(
            'select link from Task '
            f'where assignments any (resource.username = "{self.session.api_user}")'
        )

        formattedTasks = [
            dict(
                {
                    'title': task['name'],
                    'description': self._getPath(task),
                    'data': task,
                }
            )
            for task in assigned_tasks
        ]

        formattedTasks = sorted(
            formattedTasks, key=operator.itemgetter('description', 'title')
        )

        for task in formattedTasks:
            self.assignedTimeLogList.addItem(task)

    def _getPath(self, entity):
        '''Return path to *entity*.'''
        parents = entity['ancestors']
        project = entity['project']['name']
        path = [parent['name'] for parent in parents]
        path.insert(0, project)
        return ' / '.join(path)

    def getName(self):
        '''Return name of widget.'''
        return 'Track Time'

    def enableTimer(self):
        '''Enable the timer widget.'''
        self._timerEnabled = True
        self.timer_place_holder.setHidden(True)

    def disableTimer(self):
        '''Disable the timer widget.'''
        self._timerEnabled = False
        self.timer_place_holder.setHidden(False)

    def toggleTimer(self):
        '''Toggle whether timer is enabled or not.'''

        if self._timerEnabled:
            self.disableTimer()
        else:
            self.enableTimer()

    def startTime(self, data):
        self.user.start_timer(self._activeEntity, force=True)

    def _onSelectTimeLog(self, timeLog):
        '''Handle time log selection.'''
        if timeLog:
            self._timelog = timeLog
            entity = timeLog.data()
            if entity == self._activeEntity:
                return

            # Stop current timer to ensure value persisted.
            try:
                self.timer.stop()
            except ftrack_connect.error.InvalidStateError as error:
                # logger.error(error)
                pass

            # TODO: Store on Timer as data.
            self._activeEntity = entity

            if self._activeEntity:
                loggedHoursToday = 0
                timeReport = self._activeEntity['time_logged']

                timeLogValue = {
                    'title': timeLog.title(),
                    'description': timeLog.description(),
                    'time': timeReport,
                }

                self.timer.setValue(timeLogValue)
                self.user.start_timer(self._activeEntity, force=True)
                self.enableTimer()
                self.timer.start()
            else:
                self.disableTimer()
        else:
            self.disableTimer()

    def _onCommitTime(self, time):
        '''Commit *time* value to backend..'''
        if self._activeEntity:
            try:
                timelog = self.user.stop_timer()
            except Exception as error:
                logger.debug(error)
            else:
                self.session.commit()


def get_version_information(event):
    '''Return version information for ftrack connect plugin.'''
    return [
        dict(name='ftrack-connect-timetracker-widget', version=__version__)
    ]


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return
    plugin = ftrack_connect.ui.application.ConnectWidgetPlugin(TimeTracker)
    plugin.register(session, priority=50)
    logger.debug('Plugin registered')

    # Enable plugin info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
