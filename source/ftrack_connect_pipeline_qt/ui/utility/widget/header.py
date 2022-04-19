# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    thumbnail,
    circular_button,
)

# Cache of user names.
NAME_CACHE = dict()


class Header(QtWidgets.QFrame):
    '''Header widget with name and thumbnail.'''

    publishClicked = QtCore.Signal()

    def __init__(
        self,
        session,
        title=None,
        show_logo=True,
        show_user=True,
        show_publisher=False,
        parent=None,
    ):
        '''Instantiate the header widget for a user with *username*.'''

        super(Header, self).__init__(parent=parent)

        self.session = session
        self._show_logo = show_logo
        self._title = title
        self._show_publisher = show_publisher
        self._show_user = show_user
        self.setObjectName('ftrack-header-widget')

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(8, 2, 7, 8)
        self.layout().setAlignment(QtCore.Qt.AlignTop)

    def build(self):
        # Logo & User ID
        self.id_container = QtWidgets.QWidget(self)
        self.id_container_layout = QtWidgets.QHBoxLayout()
        self.id_container_layout.setContentsMargins(1, 1, 1, 1)
        self.id_container_layout.setSpacing(5)
        self.id_container_layout.setAlignment(QtCore.Qt.AlignTop)
        self.id_container.setLayout(self.id_container_layout)

        self.logo = Logo(self)
        if len(self._title or ''):
            self._title_label = QtWidgets.QLabel(self._title)
            self._title_label.setObjectName('h2')
        self.content_container = QtWidgets.QWidget()
        self.content_container.setLayout(QtWidgets.QHBoxLayout())
        self.content_container.layout().setContentsMargins(0, 0, 0, 0)
        self.content_container.layout().setSpacing(0)
        self._open_publisher_button = circular_button.CircularButton(
            'publish', '#79DFB6'
        )
        self.user = User(self.session, parent=self.parent())

        self.id_container_layout.addWidget(self.logo)
        if len(self._title or ''):
            self.id_container_layout.addWidget(self._title_label)
        self.id_container_layout.addWidget(self.content_container, 1000)
        self.id_container_layout.addWidget(self._open_publisher_button)
        self.id_container_layout.addWidget(self.user)

        # Add (Logo & User ID) & Message
        self.layout().addWidget(self.id_container)

    def post_build(self):
        self._open_publisher_button.clicked.connect(self._on_publisher_clicked)
        self.logo.setVisible(self._show_logo)
        self._open_publisher_button.setVisible(self._show_publisher)
        self.user.setVisible(self._show_user)

    def _on_publisher_clicked(self):
        self.publishClicked.emit()


class Logo(QtWidgets.QLabel):
    '''Logo widget.'''

    def __init__(self, parent=None):
        '''Instantiate logo widget.'''
        super(Logo, self).__init__(parent=parent)

        self.setObjectName('ftrack-logo-widget')

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(QtCore.Qt.AlignTop)

    def build(self):
        # logoPixmap = QtGui.QPixmap(':ftrack/image/default/ftrackLogoLabel')
        resource_path = ':ftrack/image/default/connectLogoDark'
        logoPixmap = QtGui.QPixmap(resource_path)
        if not logoPixmap is None:
            self.setPixmap(
                logoPixmap.scaled(
                    QtCore.QSize(106, 32),
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )
            )
        else:
            self.setText("ftrack")


class User(QtWidgets.QFrame):
    '''User name and logo widget.'''

    def __init__(self, session, parent=None):
        '''Instantiate user name and logo widget using *username*.'''

        super(User, self).__init__(parent=parent)
        self.session = session

        self.setObjectName('ftrack-userid-widget')

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setAlignment(QtCore.Qt.AlignRight)

    def build(self):
        username = self.session.api_user
        # self.label = QtWidgets.QLabel(self)
        self.image = thumbnail.User(self.session, parent=self.parent())
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


class MessageBox(QtWidgets.QWidget):
    '''Message widget.'''

    def __init__(self, parent=None):
        '''Instantiate message widget.'''

        super(MessageBox, self).__init__(parent=parent)
        self.setObjectName('ftrack-message-box')

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(QtCore.Qt.AlignTop)

    def build(self):
        self.label = QtWidgets.QLabel(parent=self.parent())
        self.label.resize(QtCore.QSize(900, 80))

        self.icon = QtWidgets.QLabel(parent=self.parent())
        self.icon.resize(QtCore.QSize(45, 45))

        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.label.hide()
        self.label.setObjectName('ftrack-header-message-info')

        self.layout().addWidget(self.icon)
        self.layout().addStretch()

        self.layout().addWidget(self.label)

    def setMessage(self, message, level):
        '''Set *message* and *level*.'''

        class_type = 'ftrack-header-message-%s' % level

        self.label.setObjectName(class_type)

        self.setStyleSheet(self.styleSheet())
        self.label.setText(str(message))
        self.icon.setPixmap(constants.status_icons[level])
        self.icon.setVisible(True)
        self.label.setVisible(True)

    def dismissMessage(self):
        '''Dismiss the message.'''
        self.label.setText('')
        self.label.setVisible(False)
        self.icon.setText('')
        self.icon.setVisible(False)
