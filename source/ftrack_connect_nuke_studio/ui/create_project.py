# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import tempfile
import ftrack
import getpass

import FnAssetAPI.logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore

from .widget import Resolution, Fps, Workflow

from ftrack_connect import worker
from ftrack_connect_nuke_studio.ui import create_project_ui
from ftrack_connect_nuke_studio.ui.helper import (
    treeDataFactory,
    TagTreeOverlay,
    timeFromTrackItem,
    timecodeFromTrackItem,
    sourceFromTrackItem,
    is_valid_tag_structure
)

from ftrack_connect_nuke_studio.ui.tag_tree_model import TagTreeModel
from ftrack_connect_nuke_studio.ui.tag_item import TagItem
from ftrack_connect_nuke_studio.processor import config
import ftrack_connect_nuke_studio


class FTrackServerHelper(object):
    def __init__(self):
        self.server = ftrack.xmlServer
        self.workflows = [item.get('name') for item in ftrack.getProjectSchemes()]
        self.tasktypes = dict((k.get('name'), k.get('typeid')) for k in ftrack.getTaskTypes())

    def getProjectSchema(self, name):

        data = {'type':'frompath','path':name}
        project = self.server.action('get',data)
        scheme_id = project.get('projectschemeid')
        scheme_data = {'type': 'project_scheme', 'id': scheme_id }
        schema = self.server.action('get',scheme_data)
        return schema.get('name')

    def getProjectMeta(self, name, keys):
        data = {'type':'frompath','path':name}
        project = self.server.action('get',data)
        show_id = project.get('showid')
        result = {}
        for key in keys:
            value = self.getMetadata(show_id, key)
            result[key] = value
        return result

    def createShow(self, name, workflow='VFX Scheme'):
        ''' Create a show with the given name, and the given workflow
        '''
        schema_data = {'type': 'projectschemes'}
        schema_response = self.server.action('get',schema_data)
        workflow_ids = [result.get('schemeid') for result in schema_response if result.get('name') == workflow]

        if not workflow_ids:
            print 'no workflow found with name %s ' % workflow
            return

        workflow_id = workflow_ids[0]

        data = {
            'type':'show',
            'projectschemeid':workflow_id,
            'fullname':name,
            'name':name
        }
        response = self.server.action('create',data)
        return (response.get('showid'), 'show')

    def getMetadata(self, entity_id, key):
        data = {'type':'meta','id': entity_id,'key':key}
        response = self.server.action('get', data)
        return response

    def addMetadata(self, entity_type, entity_id, metadata):
        for data_key, data_value in metadata.items():
            data = {
                'type':'meta',
                'object': entity_type,
                'id': entity_id,
                'key': data_key,
                'value': data_value}

            self.server.action('set', data)


    def setEntityData(self, entity_type, entity_id, trackItem,  start, end, resolution , fps, handles):
        ''' Populate the entity data and metadata of the given entity_id and entity_type.
        '''

        data = {
            'fstart': start,
            'fend': end,
            'fps': fps,
            'resolution': '%sx%s' % (resolution.width(), resolution.height()),
            'handles': handles
        }

        in_src, out_src, in_dst, out_dst = timecodeFromTrackItem(trackItem)
        source = sourceFromTrackItem(trackItem)

        metadata = {
            'time code src In': in_src,
            'time code src Out': out_src,
            'time code dst In': in_dst,
            'time code dst Out': out_src,
            'source material': source
        }

        attributes = {
            'type':'set',
            'object': entity_type,
            'id': entity_id,
            'values':data
        }

        attribute_response = self.server.action('set', attributes)
        self.addMetadata(entity_type, entity_id, metadata)

        return attribute_response

    def _deleteAsset(self, asset_id):
        ''' Delete the give asset id.
        '''
        asset_data = {
            'type': 'delete',
            'entityType': 'asset',
            'entityId': asset_id,
        }
        try:
            self.server.action('set', asset_data)
        except ftrack.FTrackError as error:
            FnAssetAPI.logging.debug(error)

    def _renameAsset(self, asset_id, name):
        ''' Rename the give asset_id with the given name
        '''
        asset_data = {
            'type':'set',
            'object':'asset',
            'id':asset_id,
            'values': {'name': name}
        }
        try:
            self.server.action('set', asset_data)
        except ftrack.FTrackError as error:
            FnAssetAPI.logging.debug(error)
            return

    def createAsset(self, name, parent):
        ''' Create and asset with the give name and with the given parent
        '''
        parent_id, parent_type = parent

        asset_type = 'img'

        asset_data = {
            'type':'asset',
            'parent_id': parent_id,
            'parent_type': parent_type,
            'name': name,
            'assetType': asset_type
        }
        asset_response = self.server.action('create', asset_data)
        return asset_response

    def createAssetVersion(self, asset_id, parent):
        ''' Create an asset version linked to the asset_id and parent (task)
        '''
        parent_id, parent_type = parent
        version_data = {
            'type':'assetversion',
            'assetid': asset_id,
            'taskid': parent_id,
            'comment':'',
            'ispublished': True
        }

        version_response = self.server.action('create', version_data)
        version_id = version_response.get('versionid')
        self.server.action('commit', {'type': 'assetversion', 'versionid': version_id})
        return version_id

    def createEntity(self, entity_type, name, parent):
        ''' Create a new entity for the given type and name.
        '''
        parent_id, parent_type = parent
        typeid = self.tasktypes.get(name)

        data = {
            'type': entity_type,
            'parent_id': parent_id,
            'parent_type': parent_type,
            'name': name,
            'typeid': typeid
        }
        response = self.server.action('create',data)
        return response.get('taskid'), 'task'

    def checkPermissions(self, username=None):
        ''' Check the permission level of the given named user.
        '''

        allowed = ['Administrator']

        username = username or getpass.getuser()

        user_data = {
            'type': 'user',
            'id': username
        }
        try:
            user_response = self.server.action('get', user_data)
            user_id = user_response.get('userid')
            role_data = {
                'type':'roles',
                'userid': user_id
            }
            role_response = self.server.action('get ', role_data)
            roles = [role.get('name') for role in role_response]
            # requires a better understanding of relation between show and roles.
            return True

        except Exception as error:
            FnAssetAPI.logging.debug(error)
            return False



class ProjectTreeDialog(QtGui.QDialog):

    processor_ready = QtCore.Signal(object)

    def __init__(self, data=None, parent=None):
        super(ProjectTreeDialog, self).__init__(parent=parent)

        self.serverHelper = FTrackServerHelper()
        # user_is_allowed = self.serverHelper.checkPermissions()
        # if not user_is_allowed:
        #     FnAssetAPI.logging.warning(
        #         'The user does not have enough permissions to run this application.'
        #         'please check with your administrator your roles and permission level.'
        #     )
        #     return

        self.create_ui_widgets()
        self.processors = config()
        self.data = data
        self.setWindowTitle('Create ftrack project')
        self.logo_icon = QtGui.QIcon(':ftrack/image/dark/ftrackLogoColor')
        self.setWindowIcon(self.logo_icon)

        # init empty tree
        fake_root = TagItem({})
        self.tag_model = TagTreeModel(tree_data=fake_root, parent=self)

        # set the data tree asyncronus
        self.worker = worker.Worker(treeDataFactory, [self.data])
        self.worker.finished.connect(self.on_setTreeRoot)
        self.project_worker = None

        # create overlay
        self.busyOverlay = TagTreeOverlay(self.treeView)
        self.busyOverlay.hide()

        # set model
        self.treeView.setModel(self.tag_model)
        self.treeView.setAnimated(True)
        self.treeView.header().setResizeMode(QtGui.QHeaderView.ResizeMode.ResizeToContents)

        # Connect signals.
        self.pushButton_create.clicked.connect(self.on_create_project)
        self.close_button.clicked.connect(self.on_close_dialog)

        self.treeView.selectionModel().selectionChanged.connect(self.on_tree_item_selection)
        self.worker.started.connect(self.busyOverlay.show)
        self.worker.finished.connect(self.on_project_preview_done)
        self.tag_model.project_exists.connect(self.on_project_exists)
        self.spinBox_offset.valueChanged.connect(self._refresh_tree)
        self.spinBox_handles.valueChanged.connect(self._refresh_tree)
        self.processor_ready.connect(self.on_processor_ready)

        tag_strucutre_valid, reason = is_valid_tag_structure(self.data)
        if not tag_strucutre_valid:
            self.messageArea.setText('WARNING: ' + reason)
            self.pushButton_create.setEnabled(False)
            self.messageArea.setVisible(True)
        else:
            self.setDisabled(True)

            # Start populating the tree.
            self.worker.start()

    def create_ui_widgets(self):
        '''Setup ui for create dialog.'''
        self.setObjectName('CreateProject')
        self.resize(900, 640)

        self.verticalLayout_2 = QtGui.QVBoxLayout(self)
        self.verticalLayout_2.setObjectName('verticalLayout_2')

        self.groupBox = QtGui.QGroupBox('General Settings', parent=self)
        self.groupBox.setMaximumSize(QtCore.QSize(16777215, 200))
        self.groupBox.setObjectName('groupBox')

        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName('verticalLayout')

        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')

        self.label = QtGui.QLabel('Workflow', parent=self.groupBox)
        self.label.setObjectName('label')
        self.horizontalLayout.addWidget(self.label)

        self.comboBox_workflow = Workflow(self.groupBox)
        self.comboBox_workflow.setObjectName('comboBox_workflow')
        self.horizontalLayout.addWidget(self.comboBox_workflow)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.line = QtGui.QFrame(self.groupBox)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName('line')
        self.verticalLayout.addWidget(self.line)

        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName('horizontalLayout_2')

        self.resolutionLabel = QtGui.QLabel('Resolution', parent=self.groupBox)
        self.resolutionLabel.setObjectName('resolutionLabel')
        self.horizontalLayout_2.addWidget(self.resolutionLabel)

        self.comboBox_resolution = Resolution(self.groupBox)
        self.comboBox_resolution.setObjectName('comboBox_resolution')
        self.horizontalLayout_2.addWidget(self.comboBox_resolution)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName('horizontalLayout_3')

        self.fpsLabel = QtGui.QLabel('Frames Per Second', parent=self.groupBox)
        self.fpsLabel.setObjectName('label_3')
        self.horizontalLayout_3.addWidget(self.fpsLabel)

        self.comboBox_fps = Fps(self.groupBox)
        self.comboBox_fps.setObjectName('comboBox_fps')
        self.horizontalLayout_3.addWidget(self.comboBox_fps)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName('horizontalLayout_4')

        self.handlesLabel = QtGui.QLabel('Handles', parent=self.groupBox)
        self.handlesLabel.setObjectName('handlesLabel')
        self.horizontalLayout_4.addWidget(self.handlesLabel)

        self.spinBox_handles = QtGui.QSpinBox(self.groupBox)
        self.spinBox_handles.setProperty('value', 5)
        self.spinBox_handles.setObjectName('spinBox_handles')
        self.horizontalLayout_4.addWidget(self.spinBox_handles)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName('horizontalLayout_5')

        self.stratFrameOffsetLabel = QtGui.QLabel('Start frame offset', parent=self.groupBox)
        self.stratFrameOffsetLabel.setObjectName('stratFrameOffsetLabel')
        self.horizontalLayout_5.addWidget(self.stratFrameOffsetLabel)

        self.spinBox_offset = QtGui.QSpinBox(self.groupBox)
        self.spinBox_offset.setMaximum(9999)
        self.spinBox_offset.setProperty('value', 1001)
        self.spinBox_offset.setObjectName('spinBox_offset')
        self.horizontalLayout_5.addWidget(self.spinBox_offset)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.verticalLayout_2.addWidget(self.groupBox)

        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName('splitter')
        self.treeView = QtGui.QTreeView(self.splitter)
        self.treeView.setObjectName('treeView')

        self.toolBox = QtGui.QToolBox(self.splitter)
        self.toolBox.setMinimumSize(QtCore.QSize(300, 0))
        self.toolBox.setFrameShape(QtGui.QFrame.StyledPanel)
        self.toolBox.setObjectName('toolBox')

        self.verticalLayout_2.addWidget(self.splitter)

        self.messageArea = QtGui.QLabel('', parent=self)
        self.messageArea.resize(QtCore.QSize(900, 80))        
        self.messageArea.setSizePolicy(
            QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed
        )
        self.messageArea.setVisible(False)

        #: TODO: Move styling to separate css / sass files.
        self.messageArea.setStyleSheet('''
            QLabel {
                background-color: rgba(95, 58, 58, 200);
                padding: 10px;
                border: none;
            }
        ''')
        self.verticalLayout_2.addWidget(self.messageArea)

        self.bottom_button_layout = QtGui.QHBoxLayout()
        self.verticalLayout_2.addLayout(self.bottom_button_layout)

        self.close_button = QtGui.QPushButton('Close', parent=self)
        self.bottom_button_layout.addWidget(self.close_button)

        self.pushButton_create = QtGui.QPushButton('Create', parent=self)
        self.pushButton_create.setObjectName('pushButton_create')
        self.bottom_button_layout.addWidget(self.pushButton_create)

        QtCore.QMetaObject.connectSlotsByName(self)

    def on_project_exists(self, name):
        if self.comboBox_workflow.isEnabled():

            schema = self.serverHelper.getProjectSchema(name)
            index = self.comboBox_workflow.findText(schema)
            self.comboBox_workflow.setCurrentIndex(index)
            self.comboBox_workflow.setDisabled(True)

            project_metadata = self.serverHelper.getProjectMeta(name, ['fps', 'resolution', 'offset', 'handles'])
            fps = project_metadata.get('fps')
            handles = project_metadata.get('handles')
            offset = project_metadata.get('offset')
            resolution = project_metadata.get('resolution')

            self.comboBox_resolution.setCurrentFormat(resolution)

            fps_index = self.comboBox_fps.findText(fps)
            self.comboBox_fps.setCurrentIndex(fps_index)

            self.spinBox_handles.setValue(int(handles))

            self.spinBox_offset.setValue(int(offset))

    def on_project_preview_done(self):
        ''' Slot which will be called once the project preview have started populating.
        '''

        self.setEnabled(True)

    def on_processor_ready(self, args):
        ''' signal wich will be collecting the infomrations coming from the event and trigger the processor.
        '''
        plugins = ftrack_connect_nuke_studio.PROCESSOR_PLUGINS
        processor = args[0]
        data = args[1]
        plugin = plugins.get(processor)
        plugin.process(data)

    def on_setTreeRoot(self):
        ''' signal wich will be used to populate the tree.
        '''
        self.busyOverlay.hide()
        self.pushButton_create.setEnabled(True)
        self.tag_model.setRoot(self.worker.result)

    def on_tree_item_selection(self, selected, deselected):
        ''' signal triggered when a tree item gets selected.
        '''
        self._reset_processors()

        index = selected.indexes()[0]
        item = index.model().data(index, role=self.tag_model.ITEM_ROLE)
        processor = self.processors.get(item.name)

        if not processor:
            return

        asset_names = processor.keys()
        for asset_name in asset_names:
            widget = QtGui.QWidget()
            layout = QtGui.QVBoxLayout()
            widget.setLayout(layout)

            for component_name, component_fn in processor[asset_name].items():

                data = QtGui.QGroupBox(component_name)
                data_layout = QtGui.QVBoxLayout()
                data.setLayout(data_layout)

                layout.addWidget(data)
                for node_name, knobs in component_fn.defaults.items():
                    for knob, knob_value in knobs.items():
                        knob_layout = QtGui.QHBoxLayout()
                        label = QtGui.QLabel('%s:%s' % (node_name, knob))
                        value = QtGui.QLineEdit(str(knob_value))
                        value.setDisabled(True)
                        knob_layout.addWidget(label)
                        knob_layout.addWidget(value)
                        data_layout.addLayout(knob_layout)

            self.toolBox.addItem(widget, asset_name)

    def on_close_dialog(self):
        '''Signal trigged when close dialog button is pressed.'''
        self.reject()

    def on_create_project(self):
        ''' Signal triggered when the create project button gets pressed.
        '''
        items = self.tag_model.root.children
        self.project_worker = worker.Worker(self.create_project, (items, self.tag_model.root))
        self.project_worker.finished.connect(self.on_project_created)
        self.project_worker.start()

        while self.project_worker.isRunning():
            app = QtGui.QApplication.instance()
            app.processEvents()

        if self.project_worker.error:
            raise self.project_worker.error[1], None, self.project_worker.error[2]

        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        self.setDisabled(True)

    def on_project_created(self):
        ''' Signal triggered when the project creation finishes,
        '''
        QtGui.QApplication.restoreOverrideCursor()
        QtGui.QMessageBox.information(self, "Done!", "The project has now been created\nPlease wait for the background processes to finish.");
        self.setDisabled(False)

    def _refresh_tree(self):
        ''' Helper function to force the tree to refresh.
        '''
        self.tag_model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def _reset_processors(self):
        ''' Helper function to reset the processor widgets.
        '''
        while self.toolBox.count() > 0:
            self.toolBox.removeItem(0)

    def create_project(self, data, previous=None):
        ''' Recursive function to create a new ftrack project on the server.
        '''
        selected_workflow = self.comboBox_workflow.currentText()
        for datum in data:

            # gather all the useful informations from the track
            track_in = int(datum.track.sourceIn())
            track_out = int(datum.track.sourceOut())
            source = sourceFromTrackItem(datum.track)
            start, end, in_, out = timeFromTrackItem(datum.track, self)
            fps = self.comboBox_fps.currentText()
            resolution = self.comboBox_resolution.currentFormat()
            offset = self.spinBox_offset.value()
            handles = self.spinBox_handles.value()

            if datum.type == 'show':
                if datum.exists:
                    FnAssetAPI.logging.debug('%s %s exists as %s, reusing it.' % (datum.name, datum.type, datum.exists.get('showid')))
                    result = (datum.exists.get('showid'), 'show')
                else:
                    FnAssetAPI.logging.debug('creating show %s' % datum.name)
                    result = self.serverHelper.createShow(datum.name, selected_workflow)
                    datum.exists = {'showid': result[0]}

                show_meta = {
                    'fps': fps,
                    'resolution': str(resolution),
                    'offset': offset,
                    'handles': handles
                }

                self.serverHelper.addMetadata(result[1], result[0], show_meta)

            else:
                if datum.exists:
                    FnAssetAPI.logging.debug('%s %s exists as %s, reusing it.' % (datum.name, datum.type, datum.exists.get('taskid')))
                    result = (datum.exists.get('taskid'), 'task')
                else:
                    FnAssetAPI.logging.debug('creating %s %s' % (datum.type, datum.name))
                    try:
                        result = self.serverHelper.createEntity(datum.type, datum.name, previous)
                    except ftrack.api.ftrackerror.PermissionDeniedError as error:
                        datum.exists = 'error'
                        continue
                    datum.exists = {'taskid': result[0]}

                if datum.type == 'shot':
                    FnAssetAPI.logging.debug('Setting metadata to %s' % datum.name)
                    self.serverHelper.setEntityData(result[1], result[0], datum.track, start, end, resolution , fps, handles)

                if datum.type == 'task':
                    processor = self.processors.get(datum.name)

                    if not processor:
                        continue

                    asset_names = processor.keys()
                    for asset_name in asset_names:
                        asset = self.serverHelper.createAsset(asset_name, previous)
                        asset_id = asset.get('assetid')

                        version_id = self.serverHelper.createAssetVersion(asset_id, result)

                        for component_name, component_fn in processor[asset_name].items():
                            out_data = {
                                'resolution': resolution,
                                'source_in': track_in,
                                'source_out': track_out,
                                'source_file': source,
                                'destination_in': start,
                                'destination_out': end,
                                'fps': fps,
                                'offset': offset,
                                'asset_version_id': version_id,
                                'component_name': component_name,
                                'handles': handles
                                }

                            processor_name = component_fn.getName()
                            data = (processor_name,  out_data)
                            self.processor_ready.emit(data)

            self._refresh_tree()

            if datum.children:
                self.create_project(datum.children, result)
