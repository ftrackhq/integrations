# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from functools import partial

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget


from Qt import QtWidgets

import ftrack_api


class HoudiniAbcPublisherExporterOptionsWidget(BaseOptionsWidget):
    auto_fetch_on_init = True
    OPTIONS = {
        'ABCAnimation': {
            'type': 'checkbox',
            'label': 'Include animation',
            'default': True,
        },
        'ABCFrameRangeStart': {
            'type': 'line',
            'label': 'Frame range start',
            'default_option': 'frameStart',
        },
        'ABCFrameRangeEnd': {
            'type': 'line',
            'label': 'Frame range end',
            'default_option': 'frameEnd',
        },
        'ABCFrameRangeBy': {
            'type': 'line',
            'label': 'Evaluate every',
            'default': '1.0',
        },
    }

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
        self.widgets = {}

        super(HoudiniAbcPublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(HoudiniAbcPublisherExporterOptionsWidget, self).build()

        for name, option in self.OPTIONS.items():
            default = None

            if option['type'] == 'checkbox':
                self.layout().addWidget(QtWidgets.QLabel(option['label']))
                widget = QtWidgets.QCheckBox(option['label'])
            elif option['type'] == 'combobox':
                self.layout().addWidget(QtWidgets.QLabel(option['label']))
                widget = QtWidgets.QComboBox()
                for item in option['options']:
                    widget.addItem(item['label'])
            elif option['type'] == 'line':
                widget = QtWidgets.QLineEdit()

            self.widgets[name] = widget
            self.layout().addWidget(widget)

    def current_index_changed(self, name, label):
        for item in self.OPTIONS[name]['options']:
            if item['label'] == label:
                self.set_option_result(item['value'], name)

    def post_build(self):
        super(HoudiniAbcPublisherExporterOptionsWidget, self).post_build()

        for name, widget in self.widgets.items():
            option = self.OPTIONS[name]

            if name in self.options:
                default = self.options[name]
            else:
                default_option = option.get('default_option')
                default = None
                if 0 < len(default_option or ''):
                    # Replace with that option's current value
                    default = self.options[default_option]
                if len(default or '') == 0:
                    default = option.get('default')

            update_fn = partial(self.set_option_result, key=name)
            if option['type'] == 'checkbox':
                if default is not None:
                    widget.setChecked(default)
                widget.stateChanged.connect(update_fn)
            elif self.OPTIONS[name]['type'] == 'combobox':
                if default is not None:
                    idx = 0
                    for item in option['options']:
                        if (
                            item['value'] == default
                            or item['label'] == default
                        ):
                            widget.setCurrentIndex(idx)
                        idx += 1
                update_fn = partial(self.current_index_changed, name)
                widget.currentIndexChanged.connect(update_fn)
            elif option['type'] == 'line':
                if default is not None:
                    widget.setText(default)
                widget.textChanged.connect(update_fn)

    def _reset_default_animation_options(self):
        pass


class HoudiniAbcPublisherExporterOptionsPluginWidget(
    plugin.HoudiniPublisherExporterPluginWidget
):
    plugin_name = 'houdini_abc_publisher_exporter_options'
    widget = HoudiniAbcPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniAbcPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
