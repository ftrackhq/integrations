# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import getpass
import collections
import logging

import hiero
from PySide import QtGui, QtCore

from .widget.project_selector import ProjectSelector
from .widget.fps import Fps
from .widget.workflow import Workflow
from .widget.resolution import Resolution


import ftrack
from ftrack_connect import worker
import ftrack_api.exception
import ftrack_connect.session
import ftrack_connect.ui.widget.header
import ftrack_connect_nuke_studio.exception
import ftrack_connect_nuke_studio.entity_reference

from ftrack_connect_nuke_studio.ui.helper import (
    tree_data_factory,
    TagTreeOverlay,
    time_from_track_item,
    timecode_from_track_item,
    source_from_track_item,
    validate_tag_structure
)

from ftrack_connect_nuke_studio.ui.tag_tree_model import TagTreeModel
from ftrack_connect_nuke_studio.ui.tag_item import TagItem
from ftrack_connect.ui.theme import applyTheme


def gather_processors(name, type):
    '''Retrieve processors from *name* and *type* grouped by asset name.'''
    processors = ftrack.EVENT_HUB.publish(
        ftrack.Event(
            topic='ftrack.processor.discover',
            data=dict(
                name=name,
                object_type=type
            )
        ),
        synchronous=True
    )
    return processors


class ProjectTreeDialog(QtGui.QDialog):
    '''Create project dialog.'''

    processor_ready = QtCore.Signal(object)

    update_entity_reference = QtCore.Signal(object, object, object)

    def __init__(self, data=None, parent=None, sequence=None):
        '''Initiate dialog and create ui.'''
        super(ProjectTreeDialog, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = ftrack_connect.session.get_session()

        self._cached_type_and_status = dict()
        applyTheme(self, 'integration')

        self.sequence = sequence

        self.create_ui_widgets()

        self.data = data
        self.setWindowTitle('Export project')
        self.logo_icon = QtGui.QIcon(':ftrack/image/dark/ftrackLogoColor')
        self.setWindowIcon(self.logo_icon)

        asset_type = self.session.query('AssetType where short is img').one()
        self.asset_type_id = asset_type['id']
        # Force session to cache name for all types since we will
        # be using name in get_type_and_status_from_name.
        self.session.query('select name, id from Type').all()

        # Create tree model with fake tag.
        fake_root = TagItem({})
        self.tag_model = TagTreeModel(tree_data=fake_root, parent=self)

        # Set the data tree asyncronus.
        self.worker = worker.Worker(
            tree_data_factory, [self.data, self.get_project_tag()]
        )
        self.worker.finished.connect(self.on_set_tree_root)
        self.project_worker = None

        # Create overlay.
        self.busy_overlay = TagTreeOverlay(self)
        self.busy_overlay.hide()

        # Set model to the tree view.
        self.tree_view.setModel(self.tag_model)
        self.tree_view.setAnimated(True)
        self.tree_view.header().setResizeMode(
            QtGui.QHeaderView.ResizeMode.ResizeToContents)

        # Connect signals.
        self.update_entity_reference.connect(self.on_update_entity_reference)

        self.export_project_button.clicked.connect(self.on_export_project)
        self.close_button.clicked.connect(self.on_close_dialog)

        self.tree_view.selectionModel().selectionChanged.connect(
            self.on_tree_item_selection
        )
        self.worker.started.connect(self.busy_overlay.show)
        self.worker.finished.connect(self.on_project_preview_done)
        self.tag_model.project_exists.connect(self.on_project_exists)
        self.start_frame_offset_spinbox.valueChanged.connect(self._refresh_tree)
        self.handles_spinbox.valueChanged.connect(self._refresh_tree)
        self.processor_ready.connect(self.on_processor_ready)

        self.project_selector.project_selected.connect(
            self.update_project_tag
        )

        self.start_worker()

        self.validate()

    def on_update_entity_reference(self, track_item, entity_id, entity_type):
        '''Set *entity_id* and *entity_type* as reference on *track_item*.'''
        ftrack_connect_nuke_studio.entity_reference.set(
            track_item, entity_id=entity_id, entity_type=entity_type
        )

    def update_project_tag(self, project_code):
        '''Update project tag on sequence with *project_code*.'''

        self.workflow_combobox.setDisabled(False)

        for tag in self.sequence.tags():
            meta = tag.metadata()
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                continue

            if tag.name() == 'project':
                meta.setValue('tag.value', project_code)
                break

        self.worker.args = [self.data, self.get_project_tag()]
        self.start_worker()

    def start_worker(self):
        '''Start worker.'''
        # Start populating the tree.
        self.worker.start()

    def get_project_tag(self):
        '''Return project tag.'''
        project_tag = hiero.core.findProjectTags(
            hiero.core.project('Tag Presets'), 'project'
        )[0].copy()

        project_meta = project_tag.metadata()

        attached_tag = None

        for tag in self.sequence.tags():
            meta = tag.metadata()
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                continue

            if tag.name() == project_tag.name():
                attached_tag = tag
                break
        else:
            project_meta.setValue('tag.value', self.sequence.project().name())
            project_meta.setValue('ftrack.id', None)
            self.sequence.addTag(project_tag)
            attached_tag = project_tag

        return attached_tag

    def get_default_settings(self):
        '''Return default settings for project.'''
        result = ftrack.EVENT_HUB.publish(
            ftrack.Event(
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
        self.resize(1024, 640)

        self.main_vertical_layout = QtGui.QVBoxLayout(self)
        self.setLayout(self.main_vertical_layout)

        self.header = ftrack_connect.ui.widget.header.Header(getpass.getuser())
        self.main_vertical_layout.addWidget(self.header, stretch=0)

        self.central_horizontal_widget = QtGui.QWidget()
        self.central_horizontal_layout = QtGui.QHBoxLayout()
        self.central_horizontal_widget.setLayout(
            self.central_horizontal_layout
        )
        self.main_vertical_layout.addWidget(
            self.central_horizontal_widget, stretch=1
        )
        # create a central widget where to contain settings group and tree

        self.splitter = QtGui.QSplitter(self)
        self.central_widget = QtGui.QWidget(self.splitter)
        self.central_layout = QtGui.QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.central_horizontal_layout.addWidget(self.central_widget, stretch=2)

        # settings
        self.group_box = QtGui.QGroupBox('General Settings')
        self.group_box.setMaximumSize(QtCore.QSize(16777215, 350))

        self.group_box_layout = QtGui.QVBoxLayout(self.group_box)

        project_tag = self.get_project_tag()
        project_tag_metadata = project_tag.metadata()

        # Create project selector and label.
        self.project_selector = ProjectSelector(
            project_name=project_tag_metadata.value('tag.value'),
            parent=self.group_box
        )
        self.group_box_layout.addWidget(self.project_selector)

        # Create Workflow selector and label.
        self.workflow_layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel('Workflow', parent=self.group_box)
        self.workflow_layout.addWidget(self.label)

        self.workflow_combobox = Workflow(self.session, self.group_box)
        self.workflow_layout.addWidget(self.workflow_combobox)

        self.workflow_combobox.currentIndexChanged.connect(self.validate)

        self.group_box_layout.addLayout(self.workflow_layout)

        default_settings = self.get_default_settings()

        self.line = QtGui.QFrame(self.group_box)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.group_box_layout.addWidget(self.line)

        self.resolution_layout = QtGui.QHBoxLayout()

        self.resolution_label = QtGui.QLabel(
            'Resolution', parent=self.group_box
        )
        self.resolution_layout.addWidget(self.resolution_label)

        self.resolution_combobox = Resolution(
            self.group_box, default_value=default_settings.get('resolution')
        )

        self.resolution_layout.addWidget(self.resolution_combobox)
        self.group_box_layout.addLayout(self.resolution_layout)

        self.label_layout = QtGui.QHBoxLayout()

        self.fps_label = QtGui.QLabel(
            'Frames Per Second', parent=self.group_box
        )
        self.label_layout.addWidget(self.fps_label)

        self.fps_combobox = Fps(
            self.group_box, default_value=default_settings.get('framerate')
        )
        self.label_layout.addWidget(self.fps_combobox)

        self.group_box_layout.addLayout(self.label_layout)

        self.handles_layout = QtGui.QHBoxLayout()

        self.handles_label = QtGui.QLabel('Handles', parent=self.group_box)
        self.handles_layout.addWidget(self.handles_label)

        self.handles_spinbox = QtGui.QSpinBox(self.group_box)
        self.handles_spinbox.setProperty('value', 0)
        self.handles_layout.addWidget(self.handles_spinbox)

        self.group_box_layout.addLayout(self.handles_layout)

        self.start_frame_offset_layout = QtGui.QHBoxLayout()

        self.start_frame_offset_label = QtGui.QLabel(
            'Start frame offset', parent=self.group_box
        )
        self.start_frame_offset_layout.addWidget(self.start_frame_offset_label)

        self.start_frame_offset_spinbox = QtGui.QSpinBox(self.group_box)
        self.start_frame_offset_spinbox.setMaximum(9999)
        self.start_frame_offset_spinbox.setProperty('value', 1001)
        self.start_frame_offset_layout.addWidget(
            self.start_frame_offset_spinbox
        )
        self.group_box_layout.addLayout(self.start_frame_offset_layout)

        self.central_layout.addWidget(self.group_box)

        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.tree_view = QtGui.QTreeView()
        self.central_layout.addWidget(self.tree_view)

        self.tool_box = QtGui.QToolBox(self.splitter)

        default_message = QtGui.QTextEdit(
            'Make a selection to see the available properties'
        )
        default_message.readOnly = True
        default_message.setAlignment(QtCore.Qt.AlignCenter)
        self.tool_box.addItem(default_message, 'Processors')
        self.tool_box.setContentsMargins(0, 15, 0, 0)
        self.tool_box.setMinimumSize(QtCore.QSize(300, 0))
        self.tool_box.setFrameShape(QtGui.QFrame.StyledPanel)

        self.central_horizontal_layout.addWidget(self.splitter, stretch=1)

        self.bottom_button_layout = QtGui.QHBoxLayout()
        self.main_vertical_layout.addLayout(self.bottom_button_layout)

        self.close_button = QtGui.QPushButton('Close', parent=self)
        self.bottom_button_layout.addWidget(self.close_button)

        self.export_project_button = QtGui.QPushButton('Export', parent=self)
        self.bottom_button_layout.addWidget(self.export_project_button)

        QtCore.QMetaObject.connectSlotsByName(self)

    def on_project_exists(self, project_name):
        '''Handle on project exists signal.

        *project_name* is the name of the project that is exists.

        '''
        if self.workflow_combobox.isEnabled():
            project = self.session.query(
                unicode(
                    'select project_schema.name, metadata from Project '
                    'where name is '
                ) + project_name
            ).one()
            index = self.workflow_combobox.findText(
                project['project_schema']['name']
            )
            self.workflow_combobox.setCurrentIndex(index)
            self.workflow_combobox.setDisabled(True)

            project_metadata = project['metadata']
            fps = str(project_metadata.get('fps'))
            handles = str(project_metadata.get('handles'))
            offset = str(project_metadata.get('offset'))
            resolution = str(project_metadata.get('resolution'))

            self.resolution_combobox.setCurrentFormat(resolution)

            fps_index = self.fps_combobox.findText(fps)
            self.fps_combobox.setCurrentIndex(fps_index)

            self.handles_spinbox.setValue(int(handles))

            self.start_frame_offset_spinbox.setValue(int(offset))

    def on_project_preview_done(self):
        '''Handle signal once the project preview have started populating.'''
        self.setEnabled(True)

    def on_processor_ready(self, args):
        '''Handle processor ready signal.'''
        processor_name = args[0]
        data = args[1]

        ftrack.EVENT_HUB.publish(
            ftrack.Event(
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

    def on_tree_item_selection(self, selected, deselected):
        '''Handle signal triggered when a tree item gets selected.'''
        self._reset_processors()

        index = selected.indexes()[0]
        item = index.model().data(index, role=self.tag_model.ITEM_ROLE)

        processor_groups = collections.defaultdict(list)
        for processor in gather_processors(item.name, item.type):
            if 'asset_name' in processor:
                group_name = 'Asset: ' + processor['asset_name']
            else:
                group_name = 'Others'
            processor_groups[group_name].append(processor)

        for group_name, processors in processor_groups.iteritems():
            widget = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()
            widget.setLayout(layout)

            for processor in processors:
                processor_name = processor['name']
                defaults = processor['defaults']

                data = QtGui.QGroupBox(processor_name)
                data_layout = QtGui.QVBoxLayout()
                data.setLayout(data_layout)

                layout.addWidget(data)
                for node_name, knobs in defaults.iteritems():
                    for knob, knob_value in knobs.items():
                        knob_layout = QtGui.QHBoxLayout()
                        label = QtGui.QLabel('%s:%s' % (node_name, knob))
                        value = QtGui.QLineEdit(str(knob_value))
                        value.setDisabled(True)
                        knob_layout.addWidget(label)
                        knob_layout.addWidget(value)
                        data_layout.addLayout(knob_layout)

            self.tool_box.addItem(widget, group_name)

    def on_close_dialog(self):
        '''Handle signal trigged when close dialog button is pressed.'''
        self.reject()

    def on_export_project(self):
        '''Handle signal triggered when the export project button is pressed.'''
        QtGui.QApplication.setOverrideCursor(
            QtGui.QCursor(QtCore.Qt.WaitCursor)
        )
        self.setDisabled(True)

        items = self.tag_model.root.children
        self.project_worker = worker.Worker(
            self.create_project, (items, self.tag_model.root)
        )
        self.project_worker.finished.connect(self.on_project_created)
        self.project_worker.finished.connect(self.busy_overlay.hide)
        self.project_worker.start()
        self.busy_overlay.show()

        while self.project_worker.isRunning():
            app = QtGui.QApplication.instance()
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
        QtGui.QApplication.restoreOverrideCursor()
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

        types = selected_workflow.get_types(object_type)

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
            statuses = selected_workflow.get_statuses(object_type)
            data = (
                types[0] if types else None,
                statuses[0] if statuses else None
            )

        self._cached_type_and_status[key] = data

        return self._cached_type_and_status[key]

    def validate(self):
        '''Validate UI and enable/disable export button based on result.'''
        try:
            # Validate tags.
            validate_tag_structure(self.data)

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

        project_schema = self.session.query(
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

    def _create_structure(self, data, previous):
        '''Create structure recursively from *data* and *previous*.

        Return metadata for processors.

        '''
        processor_data = []
        selected_workflow = self.workflow_combobox.currentItem()
        for datum in data:
            # Gather all the useful informations from the track
            track_in = int(
                datum.track.sourceIn() + datum.track.source().sourceIn()
            )
            track_out = int(
                datum.track.sourceOut() + datum.track.source().sourceOut()
            )
            if datum.track.source().mediaSource().singleFile():
                # Adjust frame in and out if the media source is a single file.
                # This fix is required because Hiero is reporting Frame in as 0
                # for a .mov file while Nuke is expecting Frame in 1.
                track_in += 1
                track_out += 1
                logging.debug(
                    'Single file detected, adjusting frame start and frame end '
                    'to {0}-{1}'.format(track_in, track_out)
                )

            source = source_from_track_item(datum.track)
            start, end, in_, out = time_from_track_item(datum.track, self)
            fps = self.fps_combobox.currentText()
            resolution = self.resolution_combobox.currentFormat()
            offset = self.start_frame_offset_spinbox.value()
            handles = self.handles_spinbox.value()

            if datum.type == 'show':
                if datum.exists:
                    logging.debug('%s %s exists as %s, reusing it.' % (
                        datum.name, datum.type, datum.exists.get('showid')))
                    current = self.session.get(
                        'Project', datum.exists.get('showid')
                    )
                else:
                    project_name = self.project_selector.get_new_name()
                    logging.debug('creating show %s' % project_name)

                    #: TODO: Handle permission denied error and communicate to
                    # end user.
                    current = self.session.create('Project', {
                        'name': project_name,
                        'full_name': project_name,
                        'project_schema_id': selected_workflow['id']
                    })

                    datum.exists = {'showid': current['id']}

                    current['metadata'] = {
                        'fps': fps,
                        'resolution': str(resolution),
                        'offset': offset,
                        'handles': handles
                    }

            else:
                if datum.exists:
                    logging.debug('%s %s exists as %s, reusing it.' % (
                        datum.name, datum.type, datum.exists.get('taskid')))
                    current = self.session.get(
                        'TypedContext', datum.exists.get('taskid')
                    )
                else:
                    logging.debug(
                        'creating %s %s' % (datum.type, datum.name))
                    object_type = datum.type.title()

                    sub_type, status = self.get_type_and_status_from_name(
                        object_type, datum.name
                    )
                    current = self.session.create(object_type, {
                        'name': datum.name,
                        'parent': previous,
                        'type': sub_type,
                        'status': status
                    })

                    #: TODO: Handle permission denied error and communicate to
                    # user.

                    datum.exists = {'taskid': current['id']}

                if datum.type == 'shot':
                    logging.debug(
                        'Setting metadata to %s' % datum.name)

                    data = {
                        'fstart': start,
                        'fend': end,
                        'fps': fps,
                        'resolution': '{0}x{1}'.format(
                            resolution.width(), resolution.height()
                        ),
                        'handles': handles
                    }

                    valid_keys = current['custom_attributes'].keys()
                    for key, value in data.items():
                        if key in valid_keys:
                            current['custom_attributes'][key] = value

                    in_src, out_src, in_dst, out_dst = timecode_from_track_item(
                        datum.track
                    )
                    source = source_from_track_item(datum.track)

                    metadata = {
                        'time code src In': in_src,
                        'time code src Out': out_src,
                        'time code dst In': in_dst,
                        'time code dst Out': out_src,
                        'source material': source
                    }

                    for key, value in metadata.items():
                        current['metadata']['key'] = value

                asset_parent_id = current['id']
                asset_task_id = None

                if datum.type == 'task':
                    asset_parent_id = previous['id']
                    asset_task_id = current['id']

                if datum.type not in ('task', 'show'):
                    # Set entity reference if the type is not task.
                    # Cannot modify tags in thread, therefore emit signal.
                    self.update_entity_reference.emit(
                        datum.track, datum.exists['taskid'], 'task'
                    )

                processors = gather_processors(datum.name, datum.type)

                if processors:
                    assets = dict()

                    for processor in processors:

                        version_id = None
                        asset_name = processor.get('asset_name')
                        if asset_name is not None:
                            if asset_name not in assets:
                                asset = self.session.create('Asset', {
                                    'name': asset_name,
                                    'context_id': asset_parent_id,
                                    'type_id': self.asset_type_id
                                })
                                asset_version = self.session.create(
                                    'AssetVersion', {
                                        'asset_id': asset['id'],
                                        'task_id': asset_task_id
                                    }
                                )
                                assets[asset_name] = asset_version['id']
                            else:
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
            self.session.commit()
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
