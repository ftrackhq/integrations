# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget


class LoadBaseWidget(BaseOptionsWidget):
    '''Base Class to represent a Load Widget'''

    load_modes = []
    max_column = 3

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        super(LoadBaseWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

        self.set_defaults()

    def build(self):
        super(LoadBaseWidget, self).build()

        if not self.load_modes:
            raise Exception('No Load Modes defined')

        # Remove open mode
        for index, mode in enumerate(self.load_modes):
            if mode.lower() == 'open':
                self.load_modes.pop(index)
                break

        self.load_text_label = QtWidgets.QLabel("Choose how to load file(s):")

        self.default_mode = self.options.get('load_mode', self.load_modes[0])
        self.default_options = self.options.get('load_options', {})
        self.button_group = QtWidgets.QButtonGroup(self)
        self.load_mode_layout = QtWidgets.QGridLayout()
        self.load_mode_layout.setSpacing(0)
        row_col = (0, 0)
        for mode in self.load_modes:
            p_b = ModeButton(mode)
            self.button_group.addButton(p_b)
            self.load_mode_layout.addWidget(p_b, row_col[0], row_col[1])
            if row_col[1] == self.max_column - 1:
                row_col = (row_col[0] + 1, 0)
            else:
                row_col = (row_col[0], row_col[1] + 1)

        self.layout().addWidget(self.load_text_label)
        self.layout().addLayout(self.load_mode_layout)
        # self.layout().addLayout(QtWidgets.QLabel(''))

    def post_build(self):
        super(LoadBaseWidget, self).post_build()

        self.button_group.buttonClicked.connect(self._on_load_mode_changed)

    def set_defaults(self):
        '''Set the pre selected default load mode'''
        for button in self.button_group.buttons():
            if button.text() == self.default_mode:
                button.setChecked(True)
                self._on_load_mode_changed(button)

    def _on_load_mode_changed(self, clicked_radio_button):
        '''set the result options of value for the key.'''
        self.set_option_result(clicked_radio_button.text(), key='load_mode')
        for radio_button in self.button_group.buttons():
            # Background style cannot be applied, has to be done manually
            radio_button.setStyleSheet(
                'background-color: {}'.format(
                    '#2D2C38'
                    if radio_button == clicked_radio_button
                    else 'transparent'
                )
            )


class ModeButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(ModeButton, self).__init__(label, parent=parent)
        self.setAutoExclusive(True)
        self.setCheckable(True)
