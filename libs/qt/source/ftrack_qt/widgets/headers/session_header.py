# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore, QtWidgets, QtGui

from ftrack_qt.widgets.logos import FtrackLogo as Logo
from ftrack_qt.widgets.user import FtrackUser as User


class SessionHeader(QtWidgets.QFrame):
    '''Header widget with name and thumbnail'''

    def __init__(
        self,
        session,
        title=None,
        show_logo=True,
        show_user=True,
        parent=None,
    ):
        '''
        Instantiate the header widget

        :param session: :class:`ftrack_api.session.Session` instance
        :param title: (Optional) The title to put in header
        :param show_logo: If True, Connect logo should be displayed
        :param show_user: If True, the user avatar icon should be displayed
        :param parent: The parent dialog or frame
        '''
        super(SessionHeader, self).__init__(parent=parent)

        self.session = session
        self._show_logo = show_logo
        self._title = title
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

        self.user = User(self.session)

        self.id_container_layout.addWidget(self.logo)
        if len(self._title or ''):
            self.id_container_layout.addWidget(self._title_label)
        self.id_container_layout.addWidget(self.content_container, 1000)
        self.id_container_layout.addWidget(self.user)

        # Add (Logo & User ID) & Message
        self.layout().addWidget(self.id_container)

    def post_build(self):
        self.logo.setVisible(self._show_logo)
        self.user.setVisible(self._show_user)

    def add_widget(self, widget):
        self.content_container.layout().addWidget(widget)
