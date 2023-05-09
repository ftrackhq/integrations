# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets, QtGui


class Footer(QtWidgets.QFrame):
    '''Widget for displaying information in dialog footers'''

    def __init__(self, session, show_location_stats=True, parent=None):
        '''Instantiate the header widget for a user with *username*.'''

        super(Footer, self).__init__(parent=parent)

        self.session = session
        self._show_location_stats = show_location_stats

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(10, 1, 10, 1)
        self.layout().setSpacing(1)

    def build(self):
        if self._show_location_stats:
            label = 'Location: - not set -'
            tooltip = 'Setup a storage scenario to enable file management within ftrack.'
            location = self.session.pick_location()
            if location:
                label = 'Location: {}'.format(location['name'])
                tooltip = 'Priority: {}.'.format(location.priority)
                if location.accessor:
                    label += ' | accessor: {}'.format(
                        location.accessor.__module__
                    )
                    if hasattr(location.accessor, 'prefix'):
                        label += ' @ {}'.format(location.accessor.prefix)
                        tooltip += ' Files will be published and loaded within this base directory.'
                    else:
                        tooltip += ' Files will be published and loaded with this storage accessor.'
                if location.structure:
                    label += ' | structure: {}'.format(
                        location.structure.__module__
                    )
                    tooltip += (
                        ' File structure will be dictated by this structure.'
                    )
            self._location_info_label = QtWidgets.QLabel(label)
            self._location_info_label.setToolTip(
                '{}\n{}'.format(label, tooltip)
            )
            self.layout().addWidget(self._location_info_label)

        self.layout().addWidget(QtWidgets.QLabel(), 10)
