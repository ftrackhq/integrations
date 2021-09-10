# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtCore, QtWidgets


class LoadBaseWidget(BaseOptionsWidget):
    ''' Base Class to represent a Load Widget'''
    load_modes = []

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context_id=None, asset_type_name=None
    ):
        super(LoadBaseWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context_id=context_id,
            asset_type_name=asset_type_name
        )

        self.set_defaults()

    def build(self):
        super(LoadBaseWidget, self).build()

        if not self.load_modes:
            raise Exception('No Load Modes defined')

        self.default_mode = self.options.get('load_mode', self.load_modes[0])
        self.default_options = self.options.get('load_options', {})
        self.button_group = QtWidgets.QButtonGroup(self)
        self.load_mode_layout = QtWidgets.QGridLayout()
        row_col = (0, 0)
        for mode in self.load_modes:
            p_b = QtWidgets.QPushButton(mode)
            p_b.setAutoExclusive(True)
            self.button_group.addButton(p_b)
            self.load_mode_layout.addWidget(p_b, row_col[0], row_col[1])
            if row_col[1] < 2:
                row_col = (row_col[0], row_col[1]+1)
            else:
                row_col = (row_col[0]+1, 0)

        self.layout().addLayout(self.load_mode_layout)

    def post_build(self):
        super(LoadBaseWidget, self).post_build()

        self.button_group.buttonClicked.connect(
            self._on_load_mode_changed
        )

    def set_defaults(self):
        ''' Set the pre selected default load mode'''
        for button in self.button_group.buttons():
            if button.text() == self.default_mode:
                button.setChecked(True)
                self._on_load_mode_changed(button)

    def _on_load_mode_changed(self, radio_button):
        '''set the result options of value for the key.'''
        self.set_option_result(radio_button.text(), key='load_mode')
