# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtCore, QtWidgets


class LoadBaseWidget(BaseOptionsWidget):
    load_modes = []

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):
        super(LoadBaseWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )

        self.set_defaults()

    def build(self):
        super(LoadBaseWidget, self).build()

        self.default_mode = self.options.get('load_mode', self.load_modes[0])
        self.default_options = self.options.get('load_options', {})
        self.button_group = QtWidgets.QButtonGroup(self)
        grid_lay = QtWidgets.QGridLayout()
        col_row = (0, 0)
        for mode in self.load_modes:
            r_b = QtWidgets.QRadioButton(mode)
            self.button_group.addButton(r_b)
            grid_lay.addWidget(r_b, col_row[0], col_row[1])
            if col_row[1] < 1:
                col_row = (col_row[0], col_row[1]+1)
            else:
                col_row = (col_row[0]+1, 0)

        self.layout().addLayout(grid_lay)

    def post_build(self):
        super(LoadBaseWidget, self).post_build()

        self.button_group.buttonClicked.connect(
            self._on_load_mode_changed
        )

    def set_defaults(self):
        for button in self.button_group.buttons():
            if button.text() == self.default_mode:
                button.setChecked(True)
                self._on_load_mode_changed(button)

    def _on_load_mode_changed(self, radio_button):
        '''set the result options of value for the key.'''
        self.set_option_result(radio_button.text(), key='load_mode')
