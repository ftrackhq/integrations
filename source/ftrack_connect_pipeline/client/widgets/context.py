# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from qtpy import QtWidgets
from ftrack_connect_pipeline.client.widgets.simple import BaseWidget

from ftrack_connect_pipeline.ui.widget.context_selector import ContextSelector
from ftrack_connect_pipeline.ui.widget.asset_selector import AssetSelector


class PublishContextWidget(BaseWidget):
    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        self.context = session.get('Context', options['context_id'])
        self.asset_type = options.get('asset_type')
        super(PublishContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)
        self.asset_selector.set_context(self.context)

    def build(self):
        '''build function widgets.'''
        super(PublishContextWidget, self).build()
        self._build_context_id_selector()
        self._build_asset_selector()

    def post_build(self):
        '''hook events'''
        self.context_selector.entityChanged.connect(self._on_context_changed)

    def _on_context_changed(self, context):
        self.set_option_result(context['id'], key='context_id')
        self.asset_selector.set_context(context)

    def _build_context_id_selector(self):
        self.context_layout = QtWidgets.QHBoxLayout()
        self.context_layout.setContentsMargins(0, 0, 0, 0)

        self.layout().addLayout(self.context_layout)
        self.context_selector = ContextSelector(self.session)
        self.context_selector.setEntity(self.context)

        self.context_layout.addWidget(self.context_selector)

    def _build_asset_selector(self):
        self.asset_layout = QtWidgets.QHBoxLayout()
        self.asset_layout.setContentsMargins(0, 0, 0, 0)

        self.asset_selector = AssetSelector(self.session, self.asset_type)
        self.asset_layout.addWidget(self.asset_selector)
        self.layout().addLayout(self.asset_layout)



class LoadContextWidget(BaseWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        # self._connector_wrapper = ConnectorWrapper(session)
        super(LoadContextWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)