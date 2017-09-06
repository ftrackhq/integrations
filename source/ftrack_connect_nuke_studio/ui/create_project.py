# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import getpass
import collections
import logging

import hiero
from QtExt import QtGui, QtCore, QtWidgets

from .widget.project_selector import ProjectSelector
from .widget.fps import Fps
from .widget.workflow import Workflow
from .widget.resolution import Resolution


import ftrack
from ftrack_connect import worker
from ftrack_connect.ui.widget.overlay import (
    BlockingOverlay as _BlockingOverlay
)

import ftrack_api.exception
import ftrack_api.inspection
import ftrack_api.symbol
import ftrack_connect.session
import ftrack_connect.ui.widget.header
import ftrack_connect_nuke_studio.exception
import ftrack_connect_nuke_studio.entity_reference
from ftrack_connect_nuke_studio.ui import NUKE_STUDIO_OVERLAY_STYLE

import ftrack_connect_nuke_studio.ui.helper as ui_helper
from ftrack_connect_nuke_studio.ui.tag_tree_model import TagTreeModel
from ftrack_connect_nuke_studio.ui.tree_item import TreeItem as _TreeItem
from ftrack_connect_nuke_studio.ui.widget.template import Template

from ftrack_connect.ui.theme import applyTheme

session = ftrack_connect.session.get_shared_session()


def gather_processors(name, type, track_item):
    '''Retrieve processors for *name*, *type* and *track_item*.'''
    processors = session.event_hub.publish(
        ftrack_api.event.base.Event(
            topic='ftrack.processor.discover',
            data=dict(
                name=name,
                object_type=type,
                application_object=track_item
            )
        ),
        synchronous=True
    )
    return processors


class ProjectTreeDialog(QtWidgets.QDialog):
    '''Create project dialog.'''

    processor_ready = QtCore.Signal(object)

    update_entity_reference = QtCore.Signal(object, object, object)

    def __init__(self, data=None, parent=None, sequence=None):
        '''Initiate dialog and create ui.'''
        super(ProjectTreeDialog, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )


        self._valid_shot_custom_attribute_keys = None
        self._cached_type_and_status = dict()
        applyTheme(self, 'integration')

        self.sequence = sequence

        self.create_ui_widgets()

        self.data = data
        self.setWindowTitle('Export project')
        self.logo_icon = QtGui.QIcon(':ftrack/image/dark/ftrackLogoColor')
        self.setWindowIcon(self.logo_icon)

        asset_type = session.query(
            'AssetType where short is img').first()

        # Abort the dialog if there's no 'img' asset type defined.
        if not asset_type:
            raise RuntimeError((
                'Image Sequence (img) asset type does not exist.\n'
                "Please create it in ftrack's web interface."
            ))

        self.asset_type_id = asset_type['id']
        # Force session to cache name for all types since we will
        # be using name in get_type_and_status_from_name.
        session.query('select name, id from Type').all()

        # Create tree model with fake tag.
        fake_root = _TreeItem({})
        self.tag_model = TagTreeModel(tree_data=fake_root, parent=self)

        # Set the data tree asyncronus.
        self.worker = worker.Worker(
            ui_helper.tree_data_factory,
            [
                self.data,
                self.get_project_tag(),
                self.template_combobox.selected_template()
            ]
        )
        self.worker.finished.connect(self.on_set_tree_root)
        self.project_worker = None

        # Set model to the tree view.
        self.tree_view.setModel(self.tag_model)
        self.tree_view.setAnimated(True)
        self.tree_view.header().setResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # Create overlay.
        self.busy_overlay = ui_helper.TagTreeOverlay(self)
        self.busy_overlay.hide()

        # Connect signals.
        self.update_entity_reference.connect(self.on_update_entity_reference)

        self.export_project_button.clicked.connect(self.on_export_project)
        self.close_button.clicked.connect(self.on_close_dialog)

        selection_model = self.tree_view.selectionModel()
        selection_model.selectionChanged.connect(
            self.on_tree_item_selection
        )
        self.worker.started.connect(self.busy_overlay.show)
        self.worker.finished.connect(self.on_project_preview_done)

        self.start_frame_offset_spinbox.valueChanged.connect(
            self._refresh_tree
        )
        self.handles_spinbox.valueChanged.connect(self._refresh_tree)
        self.processor_ready.connect(self.on_processor_ready)

        self.project_selector.project_selected.connect(
            self.update_project_tag
        )

        self.template_combobox.currentIndexChanged.connect(
            self.on_template_selected
        )

        self.start_worker()

        self.validate()

        if not self.compatible_server_version():
            self.logger.warn('Incompatible server version.')

            self.blockingOverlay = _BlockingOverlay(
                self, message='Incompatible server version.'
            )

            self.blockingOverlay.setStyleSheet(NUKE_STUDIO_OVERLAY_STYLE)
            self.blockingOverlay.show()

    def compatible_server_version(self):
        '''Return if server is compatible.'''
        return 'Disk' in session.types

    def on_update_entity_reference(self, track_item, entity_id, entity_type):
        '''Set *entity_id* and *entity_type* as reference on *track_item*.'''
        ftrack_connect_nuke_studio.entity_reference.set(
            track_item, entity_id=entity_id, entity_type=entity_type
        )

    def update_project_tag(self, project_code):
        '''Update project tag on sequence with *project_code*.'''
        self.logger.debug(
            u'Update project tag, project code: {0}'.format(project_code)
        )

        self.workflow_combobox.setDisabled(True)
        self.logger.debug('Disabling Workflow Combobox')

        if self.project_selector.get_state() == self.project_selector.NEW_PROJECT:
            self.logger.debug('Enabling Workflow Combobox')
            self.workflow_combobox.setDisabled(False)

        for tag in self.sequence.tags():
            meta = tag.metadata()
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                continue

            if tag.name() == 'ftrack.project':
                meta.setValue('tag.value', project_code)
                break

        self.worker.args = [
            self.data, tag,
            self.template_combobox.selected_template()
        ]
        self.start_worker()

    def on_template_selected(self, index):
        '''Handle template selected.'''
        self.worker.args = [
            self.data, self.get_project_tag(),
            self.template_combobox.selected_template()
        ]
        self.start_worker()

    def start_worker(self):
        '''Start worker.'''
        # Start populating the tree.
        self.worker.start()

    def get_project_tag(self):
        '''Return project tag.'''
        attached_tag = None

        for tag in self.sequence.tags():
            meta = tag.metadata()
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                continue

            if tag.name() == 'ftrack.project':
                attached_tag = tag
                break
        else:
            project_tag = hiero.core.Tag('ftrack.project')
            project_tag.metadata().setValue(
                'tag.value', self.sequence.project().name()
            )
            project_tag.metadata().setValue('ftrack.id', '')
            project_tag.metadata().setValue('type', 'ftrack')
            self.sequence.addTag(project_tag)
            attached_tag = project_tag

        return attached_tag

    def get_default_settings(self):
        '''Return default settings for project.'''
        result = session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.connect.nuke-studio.get-default-settings',
                data=dict(
                    nuke_studio_project=self.sequence.project()
                )
            ),
            synchronous=True
        )

        if result:
            return result[0]

        return dict()

    def create_ui_widgets(self):
        '''Setup ui for create dialog.'''
        self.resize(1024, 1024)

        self.main_vertical_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.main_vertical_layout)

        self.header = ftrack_connect.ui.widget.header.Header(getpass.getuser())
        self.main_vertical_layout.addWidget(self.header, stretch=0)

        self.central_horizontal_widget = QtWidgets.QWidget()
        self.central_horizontal_layout = QtWidgets.QHBoxLayout()
        self.central_horizontal_widget.setLayout(
            self.central_horizontal_layout
        )
        self.main_vertical_layout.addWidget(
            self.central_horizontal_widget, stretch=1
        )
        # create a central widget where to contain settings group and tree

        self.splitter = QtWidgets.QSplitter(self)
        self.central_widget = QtWidgets.QWidget(self.splitter)
        self.central_layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.central_horizontal_layout.addWidget(self.central_widget, stretch=2)

        # settings
        self.group_box = QtWidgets.QGroupBox('General Settings')
        self.group_box.setMaximumSize(QtCore.QSize(16777215, 350))

        self.group_box_layout = QtWidgets.QVBoxLayout(self.group_box)

        project_tag = self.get_project_tag()
        project_tag_metadata = project_tag.metadata()

        # Create project selector and label.
        self.project_selector = ProjectSelector(
            project_name=project_tag_metadata.value('tag.value'),
            parent=self.group_box
        )
        self.project_selector.project_selected.connect(self.handle_project_exists)
        self.group_box_layout.addWidget(self.project_selector)

        # Create Workflow selector and label.
        self.workflow_layout = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel('Workflow', parent=self.group_box)
        self.workflow_layout.addWidget(self.label)

        self.workflow_combobox = Workflow(session, self.group_box)
        self.workflow_layout.addWidget(self.workflow_combobox)

        self.workflow_combobox.currentIndexChanged.connect(self.validate)

        self.group_box_layout.addLayout(self.workflow_layout)

        default_settings = self.get_default_settings()

        self.line = QtWidgets.QFrame(self.group_box)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.group_box_layout.addWidget(self.line)

        self.resolution_layout = QtWidgets.QHBoxLayout()

        self.resolution_label = QtWidgets.QLabel(
            'Resolution', parent=self.group_box
        )
        self.resolution_layout.addWidget(self.resolution_label)

        self.resolution_combobox = Resolution(
            self.group_box, default_value=default_settings.get('resolution')
        )

        self.resolution_layout.addWidget(self.resolution_combobox)
        self.group_box_layout.addLayout(self.resolution_layout)

        self.label_layout = QtWidgets.QHBoxLayout()

        self.fps_label = QtWidgets.QLabel(
            'Frames Per Second', parent=self.group_box
        )
        self.label_layout.addWidget(self.fps_label)

        self.fps_combobox = Fps(
            self.group_box, default_value=default_settings.get('framerate')
        )
        self.label_layout.addWidget(self.fps_combobox)

        self.group_box_layout.addLayout(self.label_layout)

        self.handles_layout = QtWidgets.QHBoxLayout()

        self.handles_label = QtWidgets.QLabel('Handles', parent=self.group_box)
        self.handles_layout.addWidget(self.handles_label)

        self.handles_spinbox = QtWidgets.QSpinBox(self.group_box)
        self.handles_spinbox.setProperty('value', 0)
        self.handles_layout.addWidget(self.handles_spinbox)

        self.group_box_layout.addLayout(self.handles_layout)

        self.start_frame_offset_layout = QtWidgets.QHBoxLayout()

        self.start_frame_offset_label = QtWidgets.QLabel(
            'Start frame offset', parent=self.group_box
        )
        self.start_frame_offset_layout.addWidget(self.start_frame_offset_label)

        self.start_frame_offset_spinbox = QtWidgets.QSpinBox(self.group_box)
        self.start_frame_offset_spinbox.setMaximum(9999)
        self.start_frame_offset_spinbox.setProperty('value', 1001)
        self.start_frame_offset_layout.addWidget(
            self.start_frame_offset_spinbox
        )
        self.group_box_layout.addLayout(self.start_frame_offset_layout)

        self.central_layout.addWidget(self.group_box)

        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        self.templates_layout = QtWidgets.QHBoxLayout()

        self.handles_label = QtWidgets.QLabel('Template', parent=self)
        self.templates_layout.addWidget(self.handles_label)

        self.template_combobox = Template(self.sequence.project(), self)
        self.templates_layout.addWidget(self.template_combobox, stretch=1)

        self.central_layout.addLayout(self.templates_layout)

        self.tree_view = QtWidgets.QTreeView()
        self.central_layout.addWidget(self.tree_view)

        self.tool_box = QtWidgets.QToolBox(self.splitter)

        default_message = QtWidgets.QTextEdit(
            'Make a selection to see the available properties'
        )
        default_message.readOnly = True
        default_message.setAlignment(QtCore.Qt.AlignCenter)
        self.tool_box.addItem(default_message, 'Processors')
        self.tool_box.setContentsMargins(0, 15, 0, 0)
        self.tool_box.setMinimumSize(QtCore.QSize(300, 0))
        self.tool_box.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.central_horizontal_layout.addWidget(self.splitter, stretch=1)

        self.bottom_button_layout = QtWidgets.QHBoxLayout()
        self.main_vertical_layout.addLayout(self.bottom_button_layout)

        self.close_button = QtWidgets.QPushButton('Close', parent=self)
        self.bottom_button_layout.addWidget(self.close_button)

        self.export_project_button = QtWidgets.QPushButton('Export', parent=self)
        self.bottom_button_layout.addWidget(self.export_project_button)

        QtCore.QMetaObject.connectSlotsByName(self)

    @property
    def valid_shot_custom_attribute_keys(self):
        '''Return list of valid custom attribute keys.'''
        if self._valid_shot_custom_attribute_keys is None:
            shot_schema = filter(
                lambda schema: schema['id'] == 'Shot', session.schemas
            )
            shot_object_type_id = (
                shot_schema[0]['properties']['object_type_id']['default']
            )
            self._valid_shot_custom_attribute_keys = [
                configuration['key'] for configuration in session.query(
                    'select key from CustomAttributeConfiguration '
                    'where entity_type is "task" and object_type_id is "{0}"'
                    .format(
                        shot_object_type_id
                    )
                )
            ]

        return self._valid_shot_custom_attribute_keys

    def handle_project_exists(self, project_name):
        '''Handle on project exists signal.

        *project_name* is the name of the project that is exists.

        '''
        # If the project exists already, disable the workflow selection.
        self.workflow_combobox.setDisabled(True)
        self.logger.debug(u'On existing project: {0}'.format(project_name))

        project = session.query(
            (
                u'select project_schema.name, metadata from Project '
                u'where name is "{0}"'
            ).format(project_name)
        ).first()

        if not project:
            return

        index = self.workflow_combobox.findText(
            project['project_schema']['name'],
            QtCore.Qt.MatchExactly
        )

        self.logger.debug(
            u'Setting current workflow index to {0} for schema {1}'
            u' and project {2}'.format(
                index, project['project_schema']['name'], project['name']
            )
        )

        self.workflow_combobox.setCurrentIndex(index)

        project_metadata = project['metadata']
        fps = project_metadata.get('fps')
        handles = project_metadata.get('handles')
        offset = project_metadata.get('offset')
        resolution = project_metadata.get('resolution')

        # If the project has been created outside of Nuke Studio
        # might not be having these attributes/

        if resolution:
            self.resolution_combobox.setCurrentFormat(str(resolution))

        if fps:
            fps_index = self.fps_combobox.findText(str(fps))
            self.fps_combobox.setCurrentIndex(fps_index)

        if handles:
            self.handles_spinbox.setValue(int(str(handles)))

        if offset:
            self.start_frame_offset_spinbox.setValue(int(str(offset)))

    def on_project_preview_done(self):
        '''Handle signal once the project preview have started populating.'''
        self.setEnabled(True)

    def on_processor_ready(self, args):
        '''Handle processor ready signal.'''
        processor_name = args[0]
        data = args[1]

        session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.processor.launch',
                data=dict(
                    name=processor_name,
                    input=data
                )
            ),
            synchronous=True
        )



    def on_set_tree_root(self):
        '''Handle signal and populate the tree.'''
        self.busy_overlay.hide()
        self.tag_model.setRoot(self.worker.result)

        # Expand all nodes in the tree view.
        self.tree_view.expandAll()

    def on_tree_item_selection(self, selected, deselected):
        '''Handle signal triggered when a tree item gets selected.'''
        self._reset_processors()

        index = selected.indexes()[0]
        item = index.model().data(index, role=self.tag_model.ITEM_ROLE)

        processor_groups = collections.defaultdict(list)
        for processor in gather_processors(item.name, item.type, item.track):
            if 'asset_name' in processor:
                group_name = 'Asset: ' + processor['asset_name']
            else:
                group_name = 'Others'
            processor_groups[group_name].append(processor)

        for group_name, processors in processor_groups.iteritems():
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            widget.setLayout(layout)

            for processor in processors:
                processor_name = processor['name']
                defaults = processor['defaults']

                data = QtWidgets.QGroupBox(processor_name)
                data_layout = QtWidgets.QVBoxLayout()
                data.setLayout(data_layout)

                layout.addWidget(data)
                for node_name, knobs in defaults.iteritems():
                    for knob, knob_value in knobs.items():
                        knob_layout = QtWidgets.QHBoxLayout()
                        label = QtWidgets.QLabel('%s:%s' % (node_name, knob))
                        value = QtWidgets.QLineEdit(str(knob_value))
                        value.setDisabled(True)
                        knob_layout.addWidget(label)
                        knob_layout.addWidget(value)
                        data_layout.addLayout(knob_layout)

            self.tool_box.addItem(widget, group_name)

    def on_close_dialog(self):
        '''Handle signal trigged when close dialog button is pressed.'''
        self.reject()

    def on_export_project(self):
        '''Handle export project signal.'''
        QtWidgets.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        self.setDisabled(True)

        ftrack_connect_nuke_studio.template.save_project_template(
            self.sequence.project(), self.template_combobox.selected_template()
        )

        items = self.tag_model.root.children
        self.project_worker = worker.Worker(
            self.create_project, (items, self.tag_model.root)
        )
        self.project_worker.finished.connect(self.on_project_created)
        self.project_worker.finished.connect(self.busy_overlay.hide)
        self.project_worker.start()
        self.busy_overlay.show()

        while self.project_worker.isRunning():
            app = QtWidgets.QApplication.instance()
            app.processEvents()

        if self.project_worker.error:
            try:
                raise self.project_worker.error[1], None, self.project_worker.error[2]
            except ftrack_connect_nuke_studio.exception.PermissionDeniedError as error:
                self.header.setMessage(error.message, 'warning')
        else:
            self.header.setMessage(
                'The project has been exported!', 'info'
            )

    def on_project_created(self):
        '''Handle signal triggered when the project creation finishes.'''
        QtWidgets.QApplication.restoreOverrideCursor()
        self.setDisabled(False)

    def _refresh_tree(self):
        '''Refresh tree.'''
        self.tag_model.dataChanged.emit(
            QtCore.QModelIndex(), QtCore.QModelIndex()
        )

    def _reset_processors(self):
        '''Reset the processor widgets.'''
        while self.tool_box.count() > 0:
            self.tool_box.removeItem(0)

    def get_type_and_status_from_name(self, object_type, name):        
        '''Return defaults as a tuple from *name* and *object_type*.'''
        key = object_type
        if object_type == 'Task':
            # Chache using name to allow per sub-type status overrides if
            # object type is a task. E.g. an animation task can have a different
            # set of statuses.
            key += '_' + name

        if key in self._cached_type_and_status:
            return self._cached_type_and_status[key]

        selected_workflow = self.workflow_combobox.currentItem()
        try:
            types = selected_workflow.get_types(object_type)
        except ValueError:
            # Catch value error if no types are available for object_type.
            types = []

        data = None
        # Tasks should have type based on the *name*.
        if object_type == 'Task':
            for _type in types:
                if _type['name'] == name:
                    statuses = selected_workflow.get_statuses(
                        object_type, _type
                    )
                    data = (_type, statuses[0])

        if data is None:
            try:
                statuses = selected_workflow.get_statuses(object_type)
            except ValueError:
                # Catch value error if no statuses are available for
                # object_type.
                statuses = []
            data = (
                types[0] if types else None,
                statuses[0] if statuses else None
            )

        self._cached_type_and_status[key] = data

        return self._cached_type_and_status[key]

    def validate(self):
        '''Validate UI and enable/disable export button based on result.'''
        try:
            # Validate workflow.
            self._validate_task_tags_against_workflow()

        except ftrack_connect_nuke_studio.exception.ValidationError as error:
            self.header.setMessage(error.message, 'warning')
            self.export_project_button.setEnabled(False)
        else:
            # All validations passed, enable export button.
            self.export_project_button.setEnabled(True)
            self.header.dismissMessage()

    def _validate_task_tags_against_workflow(self):
        '''Validate the task tags against the selected workflow.'''
        task_types = {}
        for track_data in self.data:
            for tag in track_data[1]:
                metadata = tag.metadata()
                if metadata.value('ftrack.type') == 'task':
                    task_types[metadata.value('ftrack.id')] = (
                        metadata.value('ftrack.name')
                    )

        self.logger.debug(
            'Found task type tags on track items: {0}'.format(
                task_types
            )
        )

        project_schema = session.query(
            'ProjectSchema where name is "{0}"'.format(
                self.workflow_combobox.currentText()
            )
        ).one()

        valid_task_types = project_schema.get_types('Task')
        valid_ids = [task_type['id'] for task_type in valid_task_types]
        invalid_names = []

        for type_id, type_name in task_types.items():
            if type_id not in valid_ids:
                self.logger.warning(
                    'Task type {0} is not valid for current schema.'.format(
                        type_name
                    )
                )
                invalid_names.append(type_name)

        if invalid_names:
            message = (
                u'The Task tags "{0}" are not valid for the selected workflow '
                u'"{1}".'
            ).format('", "'.join(invalid_names), project_schema['name'])

            raise ftrack_connect_nuke_studio.exception.ValidationError(
                message
            )

    def _get_or_create_asset(self, asset_name, asset_parent):
        '''Return or create an asset with *asset_name* and *asset_parent*.'''
        asset_parent_exists = not (
            ftrack_api.inspection.state(asset_parent) is
            ftrack_api.symbol.CREATED
        )

        if asset_parent_exists:
            try:
                asset = session.query(
                    u'Asset where name is "{0}" and '
                    u'context_id is "{1}" and type_id is "{2}"'
                    .format(
                        asset_name, asset_parent['id'],
                        self.asset_type_id
                    )
                ).one()

                self.logger.debug(
                    'Found existing asset: {0!r}.'.format(
                        asset['id']
                    )
                )

                return asset
            except ftrack_api.exception.NoResultFoundError:
                # Asset parent exists but there is no asset created yet.
                pass

        asset_data = {
            'name': asset_name,
            'context_id': asset_parent['id'],
            'type_id': self.asset_type_id
        }

        self.logger.debug(
            u'No existing asset found, creating new: {0!r}.'.format(
                asset_data
            )
        )

        return session.create('Asset', asset_data)

    def _create_structure(self, data, previous):
        '''Create structure recursively from *data* and *previous*.

        Return metadata for processors.

        '''
        processor_data = []
        selected_workflow = self.workflow_combobox.currentItem()

        for datum in data:

            # Skip all items under the 'Not matching template' node in the
            # model.
            if datum.id == 'not_matching_template':
                continue

            fps = self.fps_combobox.currentText()
            resolution = self.resolution_combobox.currentFormat()
            offset = self.start_frame_offset_spinbox.value()
            handles = self.handles_spinbox.value()

            if datum.type == 'show':
                if datum.exists:
                    self.logger.debug('%s %s exists as %s, reusing it.' % (
                        datum.name, datum.type, datum.exists.get('id'))
                    )

                    current = datum.exists
                else:
                    project_name = self.project_selector.get_new_name()
                    self.logger.debug('creating show %s' % project_name)

                    current = session.create('Project', {
                        'name': project_name,
                        'full_name': project_name,
                        'project_schema_id': selected_workflow['id']
                    })

                    datum.exists = current

                metadata = {
                    'fps': fps,
                    'resolution': str(resolution),
                    'offset': offset,
                    'handles': handles
                }

                for key, value in metadata.items():
                    current['metadata'][key] = value

                self.logger.debug('Commit project.')
                #: TODO: Remove this commit when the api issue with order of
                # operations is fixed.
                session.commit()

            else:

                # Gather all the useful informations from the track
                track_in = int(
                    datum.track.sourceIn() + datum.track.source().sourceIn()
                )
                track_out = int(
                    datum.track.sourceOut() + datum.track.source().sourceOut()
                )
                if (
                    hiero.core.env.get('VersionMajor') is None or
                    hiero.core.env.get('VersionString') == 'NukeStudio 10.0v1' or
                    hiero.core.env.get('VersionString') == 'NukeStudio 10.0v2'
                ):
                    if datum.track.source().mediaSource().singleFile():
                        # Adjust frame in and out if the media source is a
                        # single file. This fix is required in earlier versions
                        # since Hiero is reporting Frame in as 0 for a .mov file
                        # while Nuke is expecting Frame in 1.
                        track_in += 1
                        track_out += 1
                        self.logger.debug(
                            'Single file detected, adjusting frame start and '
                            'frame end to {0}-{1}'.format(track_in, track_out)
                        )

                source = ui_helper.source_from_track_item(datum.track)
                start, end, in_, out = ui_helper.time_from_track_item(
                    datum.track, self
                )

                if datum.exists:

                    self.logger.debug(u'%s %s exists as %s, reusing it.' % (
                        datum.name, datum.type, datum.exists.get('id')))

                    current = datum.exists
                else:
                    self.logger.debug(
                        u'creating %s %s' % (datum.type, datum.name))
                    object_type = datum.type.title()

                    sub_type, status = self.get_type_and_status_from_name(
                        object_type, datum.name
                    )
                    current = session.create(object_type, {
                        'name': datum.name,
                        'parent': previous,
                        'type': sub_type,
                        'status': status
                    })

                    datum.exists = current

                if datum.type == 'shot':
                    self.logger.debug(
                        u'Setting metadata to %s' % datum.name)

                    data = {
                        'fstart': start,
                        'fend': end,
                        'fps': fps,
                        'resolution': '{0}x{1}'.format(
                            resolution.width(), resolution.height()
                        ),
                        'handles': handles
                    }

                    for key, value in data.items():
                        if key in self.valid_shot_custom_attribute_keys:
                            current['custom_attributes'][key] = value

                    in_src, out_src, in_dst, out_dst = ui_helper.timecode_from_track_item(
                        datum.track
                    )
                    source = ui_helper.source_from_track_item(datum.track)

                    metadata = {
                        'time code src In': in_src,
                        'time code src Out': out_src,
                        'time code dst In': in_dst,
                        'time code dst Out': out_src,
                        'source material': source
                    }

                    for key, value in metadata.items():
                        current['metadata'][key] = value

                asset_parent = current
                asset_task_id = None

                if datum.type == 'task':
                    asset_parent = previous
                    asset_task_id = current['id']

                if datum.type not in ('task', 'show', 'sequence', 'shot'):
                    # Set entity reference if the type is not task.
                    # Cannot modify tags in thread, therefore emit signal.
                    self.update_entity_reference.emit(
                        datum.track, datum.exists['id'], 'task'
                    )

                self.logger.debug('Commit partial structure.')
                #: TODO: Remove this commit when the api issue with order of
                # operations is fixed.
                session.commit()

                processors = gather_processors(
                    datum.name, datum.type, datum.track
                )

                if processors:
                    assets = dict()

                    for processor in processors:

                        version_id = None
                        asset_name = processor.get('asset_name')
                        if asset_name is not None:
                            if asset_name not in assets:
                                asset = self._get_or_create_asset(
                                    asset_name,
                                    asset_parent
                                )

                                self.logger.debug(
                                    u'Creating asset version on asset with id: '
                                    u'{0!r}'.format(
                                        asset['id']
                                    )
                                )
                                asset_version = session.create(
                                    'AssetVersion', {
                                        'asset_id': asset['id'],
                                        'task_id': asset_task_id
                                    }
                                )
                                assets[asset_name] = asset_version['id']

                            version_id = assets[asset_name]

                        out_data = {
                            'resolution': resolution,
                            'source_in': track_in,
                            'source_out': track_out,
                            'source_file': source,
                            'destination_in': start,
                            'destination_out': end,
                            'fps': fps,
                            'offset': offset,
                            'entity_id': current['id'],
                            'entity_type': 'task',
                            'handles': handles,
                            'application_object': datum.track
                        }

                        if version_id:
                            out_data.update({
                                'asset_version_id': version_id,
                                'component_name': processor['name']
                            })

                        processor_name = processor['processor_name']
                        processor_data.append((processor_name, out_data))

            if datum.children:
                processor_data.extend(
                    self._create_structure(datum.children, current)
                )

        return processor_data

    def create_project(self, data, previous=None):
        '''Create project from *data*.'''
        processor_data = self._create_structure(data, previous)

        try:
            # Commit the new project.
            session.commit()
        except ftrack_api.exception.ServerError as error:
            if 'permission denied' in error.message:
                raise (
                    ftrack_connect_nuke_studio.exception.PermissionDeniedError(
                        'You are not permitted to create necessary items in '
                        'ftrack. Make sure you have necessary create / update '
                        'permissions.'
                    )
                )
            else:
                self.logger.error('Un-expected error during commit.')
                raise (
                    ftrack_connect_nuke_studio.exception.PermissionDeniedError(
                        'A server error occured while creating the project, '
                        'please check logs for more information.'
                    )
                )

        self._refresh_tree()

        # Run all processors once project has been created.
        for data in processor_data:
            self.processor_ready.emit(data)
