# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import partial

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget


class UnrealSequencePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Unreal sequence collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

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

        self.unreal_sequences = []
        super(UnrealSequencePublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def add_sequences(self):
        self.sequences_cb.clear()
        if not self.unreal_sequences:
            self.sequences_cb.setDisabled(True)
            self.sequences_cb.addItem('No suitable sequences found.')
        else:
            self.sequences_cb.setDisabled(False)
            for index, data in enumerate(self.unreal_sequences):
                self.sequences_cb.addItem(data['value'])
                if data.get('default') is True:
                    self.sequences_cb.setCurrentIndex(index)

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.unreal_sequences = result
        self.add_sequences()

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(UnrealSequencePublisherCollectorOptionsWidget, self).build()
        self.sequences_cb = QtWidgets.QComboBox()
        self.sequences_cb.setToolTip(self.description)
        self.layout().addWidget(self.sequences_cb)

        if self.options.get('sequence_name'):
            self.unreal_sequences.append(
                {'value': self.options.get('sequence_name')}
            )

        self.add_sequences()

        self.report_input()

    def post_build(self):
        super(UnrealSequencePublisherCollectorOptionsWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='sequence_name')

        self.sequences_cb.currentTextChanged.connect(update_fn)
        if self.unreal_sequences:
            self.set_option_result(
                self.sequences_cb.currentText(), key='sequence_name'
            )

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        num_objects = 1 if self.sequences_cb.isEnabled() else 0
        if num_objects > 0:
            message = '{} sequence{} selected'.format(
                num_objects, 's' if num_objects > 1 else ''
            )
            status = True
        else:
            message = 'No sequence selected!'
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class UnrealSequencePublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_sequence_publisher_collector'
    widget = UnrealSequencePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherCollectorPluginWidget(api_object)
    plugin.register()
