# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import urlparse
import getpass
import collections

from PySide import QtGui

from FnAssetAPI import logging
import nuke
import hiero.core
import ftrack_connect.crew_hub
import ftrack
import ftrack_legacy
from ftrack_connect.ui.widget import notification_list as _notification_list
from ftrack_connect.ui.widget import crew as _crew
import ftrack_connect.ui.theme

from ftrack_connect.ui.widget.header import Header


session = ftrack.Session()


class NukeCrewHub(ftrack_connect.crew_hub.SignalCrewHub):

    def isInterested(self, data):
        '''Return if interested in user with *data*.'''

        # In first version we are interested in all users since all users
        # are visible in the list.
        return True


class UserClassifier(object):
    '''Class to classify users based on your context.'''

    def __init__(self):
        '''Initialise classifier.'''
        super(UserClassifier, self).__init__()

        logging.info('Initialise classifier')

        self._lookup = dict()

        shot_ids = []
        for item in hiero.core.findItems():
            if hasattr(item, 'entityReference'):
                reference = item.entityReference()
                if reference and reference.startswith('ftrack://'):

                    url = urlparse.urlparse(reference)
                    shot_ids.append(url.netloc)

        logging.info(
            'Classifying shot ids: "{0}"'.format(
                shot_ids
            )
        )
        if shot_ids:
            tasks = session.query(
                (
                    'select assignments, name from Task where parent_id in '
                    '({0})'
                ).format(
                  ', '.join(shot_ids)
                )
            )
            for task in tasks:
                for resource in task['assignments']:
                    self._lookup[resource['resource_id']] = 'related'

        logging.info(
            '_lookup contains "{0}"'.format(str(self._lookup))
        )

    def __call__(self, user_id):
        '''Classify user and return relevant group.'''
        try:
            return self._lookup[user_id]
        except KeyError:
            return 'others'


class NukeCrew(QtGui.QDialog):

    def __init__(self, parent=None):
        '''Initialise widget with *parent*.'''
        super(NukeCrew, self).__init__(parent=parent)

        ftrack_connect.ui.theme.applyTheme(self, 'integration')

        self.setMinimumWidth(400)
        self.setSizePolicy(
            QtGui.QSizePolicy(
                QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
            )
        )

        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.horizontal_layout = QtGui.QHBoxLayout()

        self.header = Header(username=getpass.getuser(), parent=self)

        self.vertical_layout.addWidget(self.header)

        self.notification_list = _notification_list.Notification(
            self
        )

        self._hub = NukeCrewHub()

        self._classifier = UserClassifier()

        groups = ['Related']
        self.chat = _crew.Crew(
            groups, hub=self._hub, classifier=self._classifier, parent=self
        )

        for user in session.query(
            'select id, username, first_name, last_name'
            ' from User where is_active is True'
        ):
            if user['username'] != getpass.getuser():
                self.chat.addUser(
                    user['first_name'], user['id']
                )

        self.tab_panel = QtGui.QTabWidget(parent=self)
        self.tab_panel.addTab(self.chat, 'Chat')
        self.tab_panel.addTab(self.notification_list, 'Notifications')

        self.horizontal_layout.addWidget(self.tab_panel)

        # TODO: This styling should probably be done in a global stylesheet
        # for the entire Nuke plugin.
        self.notification_list.overlay.setStyleSheet('''
            BlockingOverlay {
                background-color: rgba(58, 58, 58, 200);
                border: none;
            }

            BlockingOverlay QFrame#content {
                padding: 0px;
                border: 80px solid transparent;
                background-color: transparent;
                border-image: none;
            }

            BlockingOverlay QLabel {
                background: transparent;
            }
        ''')

        self.vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.addLayout(self.horizontal_layout)

        self.setObjectName('Crew')
        self.setWindowTitle('Crew')

        # :TODO: Bind listener to refresh scene when clips are added or changed,
        # or if the selection changes.
        self.on_refresh_event()

        self._enter_chat()

    def _enter_chat(self):
        '''.'''
        user = ftrack_legacy.getUser(getpass.getuser())
        data = {
            'user': {
                'name': user.getName(),
                'id': user.getId()
            },
            'application': {
                'identifier': 'nuke',
                'label': 'Nuke {0}'.format(nuke.NUKE_VERSION_STRING)
            },
            'context': {
                'project_id': 'my_project_id',
                'containers': []
            }
        }

        self._hub.enter(data)

    def on_refresh_event(self):
        '''Handle refresh events.'''
        context = self._read_context_from_environment()
        self._update_notification_context(context)
        self._update_crew_context(context)

    def _update_notification_context(self, context):
        '''Update the notification list context on refresh.'''
        self.notification_list.clearContext(_reload=False)

        for asset in context['asset']:
            self.notification_list.addContext(asset, 'asset', False)

        for task in context['task']:
            self.notification_list.addContext(task, 'task', False)

        self.notification_list.reload()

    def _update_crew_context(self, context):
        '''Update crew context and re-classify online users.'''

    def _read_context_from_environment(self):
        '''Read context from environment.'''
        context = collections.defaultdict(list)

        #: TODO: Add contexts from scene.

        return context
