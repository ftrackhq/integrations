# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.selectors import AssetVersionSelector


class ComponentAndVersionWidget(QtWidgets.QWidget):
    '''Widget representing the asset component and version'''

    @property
    def version_selector(self):
        return self._version_selector

    def __init__(self, collapsed, parent=None):
        '''
        Initialize component & version widget

        :param collapsed: Boolean telling if widget is within collapsed accordion or not
        :param parent: the parent dialog or frame
        '''
        super(ComponentAndVersionWidget, self).__init__(parent=parent)

        self._collapsed = collapsed

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(2)

    def build(self):
        self._component_filename_widget = QtWidgets.QLabel()
        self._component_filename_widget.setObjectName('gray')
        self.layout().addWidget(self._component_filename_widget)
        delimiter_label = QtWidgets.QLabel(' - ')
        delimiter_label.setObjectName('gray')
        self.layout().addWidget(delimiter_label)

        if self._collapsed:
            self._version_nr_widget = QtWidgets.QLabel()
            self._version_nr_widget.setObjectName('color-primary')
            self.layout().addWidget(self._version_nr_widget)
        else:
            self._version_selector = AssetVersionSelector()
            self.layout().addWidget(self._version_selector)

    def set_latest_version(self, is_latest_version):
        '''Set if asset version is the latest version (*is_latest_version* is True) or not'''
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        if self._collapsed:
            self._version_nr_widget.setStyleSheet('color: {}'.format(color))
        else:
            self.version_selector.setStyleSheet(
                '''
                color: {0};
                border: 1px solid {0};
            '''.format(
                    color
                )
            )

    def set_component_filename(self, component_path):
        '''Set the component filename based on *component_path*'''
        self._component_filename_widget.setText(
            '- {}'.format(component_path.replace('\\', '/').split('/')[-1])
        )

    def set_version(self, version_nr, versions=None):
        '''Set the current version number from *version_nr*. *versions* should
        be provided if about to expand, otherwise the version will be selected
        '''
        if self._collapsed:
            self._version_nr_widget.setText('v{}'.format(str(version_nr)))
        else:
            if versions:
                self.version_selector.clear()
                for index, asset_version in enumerate(reversed(versions)):
                    self.version_selector.addItem(
                        'v{}'.format(asset_version['version']),
                        asset_version['id'],
                    )
                    if asset_version['version'] == version_nr:
                        self.version_selector.setCurrentIndex(index)
            else:
                label = 'v{}'.format(version_nr)
                for index in range(self.version_selector.count()):
                    if self.version_selector.itemText(index) == label:
                        self.version_selector.setCurrentIndex(index)
                        break
