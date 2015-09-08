# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import urlparse
import getpass
import collections
import logging

from PySide import QtGui

import nuke
import hiero.core
import hiero.core.events
import ftrack_connect_nuke_studio.crew_hub
import ftrack_api
import ftrack
from ftrack_connect.ui.widget import notification_list as _notification_list
from ftrack_connect.ui.widget import crew as _crew
import ftrack_connect.ui.theme

from ftrack_connect.ui.widget.header import Header


session = ftrack_api.Session()

NUKE_STUDIO_OVERLAY_STYLE = '''
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
'''

#: TODO: Re-run classifier when clips in timeline are assetised, added or
# removed.
class UserClassifier(object):
    '''Class to classify users based on your context.'''

    def __init__(self):
        '''Initialise classifier.'''
        super(UserClassifier, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.info('Initialise classifier')
        self._lookup = dict()

    def update_context(self, context):
        '''Update based on *context*.'''
        self._lookup = dict()

        self.logger.info(
            'Classifying based context: "{0}"'.format(context)
        )
        if context['shot']:
            tasks = session.query(
                (
                    'select assignments, name from Task where parent_id in '
                    '({0})'
                ).format(
                  ', '.join(context['shot'])
                )
            )
            for task in tasks:
                for resource in task['assignments']:
                    self._lookup[resource['resource_id']] = 'related'

        if context['asset_version']:
            versions = session.query(
                (
                    'select user from AssetVersion where id in '
                    '({0})'
                ).format(
                  ', '.join(context['asset_version'])
                )
            )
            for version in versions:
                self._lookup[version['user']['id']] = 'contributor'

        self.logger.info(
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

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.logger.debug('Apply *integration* theme.')
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

        self._hub = ftrack_connect_nuke_studio.crew_hub.crew_hub

        self._classifier = UserClassifier()

        current_user = ftrack.getUser(getpass.getuser())
        groups = ['contributor', 'related']
        self.chat = _crew.Crew(
            groups, current_user, hub=self._hub, classifier=self._classifier,
            parent=self
        )

        self.chat.chat.busyOverlay.setStyleSheet(NUKE_STUDIO_OVERLAY_STYLE)

        added_user_ids = []
        for _user in session.query(
            'select id, username, first_name, last_name'
            ' from User where is_active is True'
        ):
            if _user['id'] != current_user.getId():
                self.chat.addUser(
                    u'{0} {1}'.format(_user['first_name'], _user['last_name']),
                    _user['id']
                )

                added_user_ids.append(_user['id'])

        self.tab_panel = QtGui.QTabWidget(parent=self)
        self.tab_panel.addTab(self.chat, 'Chat')
        self.tab_panel.addTab(self.notification_list, 'Notifications')

        self.horizontal_layout.addWidget(self.tab_panel)

        # TODO: This styling should probably be done in a global stylesheet
        # for the entire Nuke plugin.
        self.notification_list.overlay.setStyleSheet(NUKE_STUDIO_OVERLAY_STYLE)

        self.vertical_layout.setContentsMargins(10, 10, 10, 10)
        self.vertical_layout.addLayout(self.horizontal_layout)

        self.setObjectName('Crew')
        self.setWindowTitle('Crew')

        hiero.core.events.registerInterest(
            'kAfterProjectLoad', self.on_refresh_event
        )

        if not self._hub.compatibleServerVersion:
            self.logger.warn('Incompatible server version.')

            self.blockingOverlay = ftrack_connect.ui.widget.overlay.BlockingOverlay(
                self, message='Incompatible server version.'
            )
            self.blockingOverlay.setStyleSheet(NUKE_STUDIO_OVERLAY_STYLE)
            self.blockingOverlay.show()
        else:
            self._hub.populateUnreadConversations(current_user.getId(), added_user_ids)

    def on_refresh_event(self, *args, **kwargs):
        '''Handle refresh events.'''

        context = self._read_context_from_environment()
        self._update_notification_context(context)
        self._update_crew_context(context)

    def _update_notification_context(self, context):
        '''Update the notification list context on refresh.'''
        self.logger.info(
            'Update notification based context: "{0}"'.format(context)
        )
        self.notification_list.clearContext(_reload=False)

        for task in context['shot']:
            self.notification_list.addContext(task, 'task', False)

        self.notification_list.reload()

    def _update_crew_context(self, context):
        '''Update crew context and re-classify online users.'''
        self._classifier.update_context(context)
        self.chat.classifyOnlineUsers()

    def _read_context_from_environment(self):
        '''Read context from environment.'''
        context = collections.defaultdict(list)

        component_ids = []
        for item in hiero.core.findItems():
            if hasattr(item, 'entityReference'):
                reference = item.entityReference()
                if reference and reference.startswith('ftrack://'):

                    url = urlparse.urlparse(reference)
                    query = urlparse.parse_qs(url.query)
                    entityType = query.get('entityType')[0]

                    if entityType == 'task':
                        context['shot'].append(url.netloc)
                    elif entityType == 'component':
                        component_ids.append(url.netloc)

        if component_ids:
            components = session.query(
                'select version.asset.context_id from Component where id in'
                ' ({0})'.format(','.join(component_ids))
            ).all()

            for component in components:
                context['shot'].append(
                    component['version']['asset']['context_id']
                )

        return context
