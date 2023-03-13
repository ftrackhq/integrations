# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore, QtGui

import ftrack_api

from ftrack_connect_pipeline_qt import plugin

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.plugin.widget.context import StatusSelector
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.ui.utility.widget.asset_selector import (
    AssetSelector,
)
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo


class TestProjectPublisherContextOptionsWidget(BaseOptionsWidget):
    '''Unreal project publisher context plugin widget'''

    statusesFetched = QtCore.Signal(object)

    @property
    def project_context_id(self):
        return self._project_context_selector.context_id

    @project_context_id.setter
    def project_context_id(self, context_id):
        self._project_context_selector.context_id = context_id
        if context_id:
            self.set_parent_context(context_id)
        # Passing project context id to options
        self.set_option_result(context_id, key='project_context_id')

    @property
    def parent_context_id(self):
        return self._parent_context_selector.context_id

    @parent_context_id.setter
    def parent_context_id(self, context_id):
        self._parent_context_selector.context_id = context_id
        # Passing parent context id to options
        self.set_option_result(context_id, key='parent_context_id')

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
        super(TestProjectPublisherContextOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def build(self):
        '''Prevent widget name from being displayed with header style.'''
        self.layout().setContentsMargins(10, 0, 0, 0)

        self.name_label = QtWidgets.QLabel(self.name.title())
        self.name_label.setToolTip(self.description)
        self.layout().addWidget(self.name_label)

        project_context_id = None
        if self.context_id:
            context = self.session.query(
                'Context where id is "{}"'.format(self.context_id)
            ).one()
            project_context_id = context.get('project_id')

            # Pass task context id to options
            self.set_option_result(self.context_id, key='context_id')

        self._project_context_selector = ContextSelector(
            self.session,
            enble_context_change=True,
            select_task=False,
            browse_context_id=project_context_id,
        )
        self.layout().addWidget(self._project_context_selector)

        self.layout().addWidget(line.Line())

        self.layout().addWidget(
            QtWidgets.QLabel(
                "Unreal {}asset build context".format(
                    ' level' if self.options.get('level') is True else ''
                )
            )
        )
        self._parent_context_selector = ContextSelector(self.session)
        self.layout().addWidget(self._parent_context_selector)

        self.layout().addWidget(line.Line())

        self.layout().addLayout(self._build_asset_selector())
        self.statusesFetched.connect(self.set_statuses)
        self.layout().addWidget(line.Line())
        version_and_comment = QtWidgets.QWidget()
        version_and_comment.setLayout(QtWidgets.QVBoxLayout())
        version_and_comment.layout().addWidget(
            QtWidgets.QLabel('Version information')
        )
        version_and_comment.layout().addLayout(self._build_status_selector())
        version_and_comment.layout().addLayout(self._build_comments_input())
        self.layout().addWidget(version_and_comment)

    def post_build(self):
        '''Post build hook.'''
        super(TestProjectPublisherContextOptionsWidget, self).post_build()
        # Fetch the Unreal project context id
        self.project_context_id = '52c53ce8-7ac7-11ed-aa03-a662eeb18ccf'  # unreal_utils.get_project_context_id()

        self._project_context_selector.entityChanged.connect(
            self.on_project_context_changed
        )
        self._parent_context_selector.changeContextClicked.connect(
            self.on_change_parent_context_clicked
        )
        self.asset_selector.assetChanged.connect(self._on_asset_changed)
        self.comments_input.textChanged.connect(self._on_comment_updated)
        self.status_selector.currentIndexChanged.connect(
            self._on_status_changed
        )

    def on_project_context_changed(self, context):
        '''Handle context change - store it with Unreal project'''
        # unreal_utils.set_project_context_id('52c53ce8-7ac7-11ed-aa03-a662eeb18ccf')
        self.project_context_id = '52c53ce8-7ac7-11ed-aa03-a662eeb18ccf'

    def on_change_parent_context_clicked(self):
        dialog.ModalDialog(
            self.parent(),
            message='The unreal project parent context is not editable.',
        )

    def set_parent_context(self, project_context_id):
        '''Set the project context for the widget to *context_id*. Make sure the corresponding project
        asset build is created and use it as the context.'''
        asset_path = None
        if self.options.get('selection') is True:
            # TODO: Fetch the selected asset in content browser
            pass
        else:
            # Fetch the current level
            pass
            # asset_path = str(
            #     unreal.EditorLevelLibrary.get_editor_world().get_path_name()
            # ).split('.')[0]

        # TODO: ask if to create the asset build before create it,
        #  otherwise we can create a mess.
        # Create asset build if it doesn't exist, will throw exception if permission problem
        try:
            # asset_build = unreal_utils.ensure_asset_build(
            #     project_context_id, asset_path, session=self.session
            # )
            # self._parent_context_selector.entity = asset_build

            # TODO: set the asset type name asset_type_name

            self.parent_context_id = 'cd6c11ea-7f7e-11ed-8af5-0e96d215a282'

            self.asset_selector.set_context(
                self.parent_context_id, self.asset_type_name
            )

        except Exception as e:
            dialog.ModalDialog(
                self.parent(),
                message='Failed to create project level asset build for asset "{}", please check your ftrack permissions and for any existing entities in conflict.\n\nDetails: {}'.format(
                    asset_path, e
                ),
            )
            raise

    def _on_status_changed(self, status):
        '''Updates the options dictionary with provided *status* when
        currentIndexChanged of status_selector event is triggered'''
        status_id = self.status_selector.itemData(status)
        self.set_option_result(status_id, key='status_id')
        self.status_selector.on_status_changed(status_id)

    def _on_comment_updated(self):
        '''Updates the option dictionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self.comments_input.toPlainText()
        self.set_option_result(current_text, key='comment')

    def _on_asset_changed(self, asset_name, asset_entity, is_valid):
        '''Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        self.set_option_result(asset_name, key='asset_name')
        self.set_option_result(is_valid, key='is_valid_name')
        if asset_entity:
            self.set_option_result(asset_entity['id'], key='asset_id')
            self.assetChanged.emit(asset_name, asset_entity['id'], is_valid)
        else:
            self.assetChanged.emit(asset_name, None, is_valid)

    def _build_asset_selector(self):
        '''Builds the asset_selector widget'''
        self.asset_layout = QtWidgets.QVBoxLayout()
        # self.asset_layout.setContentsMargins(0, 0, 0, 0)
        self.asset_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_selector = AssetSelector(self.session)
        self.asset_layout.addWidget(self.asset_selector)
        return self.asset_layout

    def _build_status_selector(self):
        '''Builds the status_selector widget'''
        self.status_layout = QtWidgets.QHBoxLayout()
        # self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setAlignment(QtCore.Qt.AlignTop)

        self.asset_status_label = QtWidgets.QLabel("Status")
        self.asset_status_label.setObjectName('gray')

        self.status_selector = StatusSelector()

        self.status_layout.addWidget(self.asset_status_label)
        self.status_layout.addWidget(self.status_selector, 10)

        self.status_layout.addStretch()

        thread = BaseThread(
            name='get_status_thread',
            target=self._get_statuses,
            callback=self.emit_statuses,
            target_args=(),
        )
        thread.start()

        return self.status_layout

    def _build_comments_input(self):
        '''Builds the comments_container widget'''
        self.coments_layout = QtWidgets.QHBoxLayout()
        self.coments_layout.setContentsMargins(0, 0, 0, 0)

        comment_label = QtWidgets.QLabel('Description')
        comment_label.setObjectName('gray')
        comment_label.setAlignment(QtCore.Qt.AlignTop)
        self.comments_input = QtWidgets.QTextEdit()
        self.comments_input.setMaximumHeight(40)
        self.comments_input.setPlaceholderText("Type a description...")
        self.coments_layout.addWidget(comment_label)
        self.coments_layout.addWidget(self.comments_input)

        self.set_option_result(
            self.comments_input.toPlainText(), key='comment'
        )
        return self.coments_layout

    def emit_statuses(self, statuses):
        '''Emit signal to set statuses on the combobox'''
        # Emit signal to add the sttuses to the combobox
        # because here we could have problems with the threads
        self.statusesFetched.emit(statuses)

    def set_statuses(self, statuses):
        '''Set statuses on the combo box'''
        self.status_selector.set_statuses(statuses)
        if statuses:
            self.set_option_result(statuses[0]['id'], key='status_id')
            self.status_selector.on_status_changed(statuses[0]['id'])

    def _get_statuses(self):
        '''Returns the status of the selected assetVersion'''
        context_entity = self.session.query(
            'select link, name, parent, parent.name from Context where id '
            'is "{}"'.format(self.parent_context_id)
        ).one()

        project = self.session.query(
            'select name, parent, parent.name from Context where id is "{}"'.format(
                context_entity['link'][0]['id']
            )
        ).one()

        schema = project['project_schema']
        statuses = schema.get_statuses('AssetVersion')
        return statuses


class TestProjectPublisherContextOptionsPluginWidget(
    plugin.PublisherContextPluginWidget
):
    '''Project publisher context widget enabling user selection'''

    plugin_name = 'test_project_publisher_context'
    widget = TestProjectPublisherContextOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = TestProjectPublisherContextOptionsPluginWidget(api_object)
    plugin.register()
