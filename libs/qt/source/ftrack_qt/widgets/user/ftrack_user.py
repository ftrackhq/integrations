# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
# TODO: Clean this code
try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.widgets.thumbnails import UserThumbnail as UserThumbnail

# Cache of user names.
NAME_CACHE = dict()


class FtrackUser(QtWidgets.QFrame):
    '''Header user avatar widget'''

    def __init__(self, session, parent=None):
        '''Instantiate user name and logo widget using *username*.'''

        super(FtrackUser, self).__init__(parent=parent)
        self.session = session

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

    def build(self):
        username = self.session.api_user
        # self.label = QtWidgets.QLabel(self)
        self.image = UserThumbnail(self.session)
        self.image.setFixedSize(35, 35)

        self.layout().addWidget(self.image)

        self.image.load(username)

        if username not in NAME_CACHE:
            user = self.session.query(
                'select first_name, last_name from User where username is "{}"'.format(
                    username
                )
            ).first()

            NAME_CACHE[username] = '{} {}'.format(
                user['first_name'], user['last_name']
            ).title()

        tooltip = 'Logged in as: {}'.format(self.session.api_user)
        tooltip += '\n'
        tooltip += 'Server: {}'.format(self.session.server_url)
        tooltip += '\n'
        location = self.session.pick_location()
        if location:
            tooltip += 'Location: {}'.format(location['name'])
            tooltip += '\n'
            tooltip += 'Priority: {}'.format(location.priority)
            tooltip += '\n'
            if location.accessor:
                tooltip += 'Accessor: {}'.format(location.accessor.__module__)
                if hasattr(location.accessor, 'prefix'):
                    tooltip += ' @ {}'.format(location.accessor.prefix)
                tooltip += '\n'
            if location.structure:
                tooltip += 'Structure: {}\n'.format(
                    location.structure.__module__
                )
        else:
            tooltip += 'Location: - not set -'
        tooltip += '\n'
        self.setToolTip(tooltip)
