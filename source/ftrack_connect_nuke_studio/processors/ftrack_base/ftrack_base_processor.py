# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import time
import tempfile
import logging

import hiero.core
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

from QtExt import QtCore, QtWidgets, QtGui

from . import FtrackBasePreset, FtrackBase, FtrackProcessorValidationError, FtrackProcessorError


class FtrackSettingsValidator(QtWidgets.QDialog):

    def __init__(self, session, error_data, missing_assets_types):

        '''
        Return a validator widget for the given *error_data* and *missing_assets_types*.
        '''

        super(FtrackSettingsValidator, self).__init__()
        self.setWindowTitle('Validation error')
        self._session = session

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        ftrack_icon = QtGui.QIcon(':/ftrack/image/default/ftrackLogoColor')
        self.setWindowIcon(ftrack_icon)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        box = QtWidgets.QGroupBox('An error occured in the current schema configuration.')

        self.layout().addWidget(box)

        box_layout = QtWidgets.QVBoxLayout()
        box.setLayout(box_layout)

        form_layout = TaskUIFormLayout()
        box_layout.addLayout(form_layout)

        for preset, values in error_data.items():
            form_layout.addDivider('Wrong {0} presets'.format(preset.name()))

            # TODO: attribute should be reversed .... as they are appearing in the wrong order
            for attribute, valid_values in values.items():
                valid_values.insert(0, '- select a value -')
                key, value, label = attribute, valid_values, ' '.join(attribute.split('_'))
                tooltip = 'Set {0} value'.format(attribute)

                uiProperty = UIPropertyFactory.create(
                    type(value),
                    key=key,
                    value=value,
                    dictionary=preset.properties()['ftrack'],
                    label=label + ':',
                    tooltip=tooltip
                )
                form_layout.addRow(label + ':', uiProperty)

        if missing_assets_types:
            form_layout.addDivider('Missing asset types')

            for missing_asset in missing_assets_types:
                create_asset_button = QtWidgets.QPushButton(
                    missing_asset.capitalize()
                )
                create_asset_button.clicked.connect(self.create_missing_asset)
                form_layout.addRow('create asset: ', create_asset_button)

        buttons = QtWidgets.QDialogButtonBox()
        buttons.setOrientation(QtCore.Qt.Horizontal)
        buttons.addButton('Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        buttons.addButton('Accept', QtWidgets.QDialogButtonBox.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)

    def create_missing_asset(self):
        sender = self.sender()
        asset_type = sender.text()
        self._session.ensure(
            'AssetType',
            {
                'short': asset_type.lower(),
                'name': asset_type
            }
        )
        try:
            self._session.commit()
        except Exception as error:
            QtWidgets.QMessageBox().critical(self, 'ERROR', str(error))
            return

        sender.setDisabled(True)


class FtrackProcessorPreset(FtrackBasePreset):
    def __init__(self, name, properties):
        super(FtrackProcessorPreset, self).__init__(name, properties)

    def set_ftrack_properties(self, properties):
        super(FtrackProcessorPreset, self).set_ftrack_properties(properties)


class FtrackProcessor(FtrackBase):
    def __init__(self, initDict):
        super(FtrackProcessor, self).__init__(initDict)

        # Store a reference of the origial initialization data.
        self._init_dict = initDict

        # Store a reference of the ftrack properties for easier access.
        self.ftrack_properties = self._preset.properties()['ftrack']

        # Note we do resolve {ftrack_version} as part of the {ftrack_asset} function.
        self.fn_mapping = {
            '{ftrack_project}': self._create_project_fragment,
            '{ftrack_sequence}': self._create_sequence_fragment,
            '{ftrack_shot}': self._create_shot_fragment,
            '{ftrack_asset}': self._create_asset_fragment,
            '{ftrack_component}': self._create_component_fragment
        }

        self._components = {}

    def timeStampString(self, localtime):
        '''timeStampString(localtime)
        Convert a tuple or struct_time representing a time as returned by gmtime() or localtime() to a string formated YEAR/MONTH/DAY TIME.
        '''
        return time.strftime('%Y/%m/%d %X', localtime)

    def _makePath(self):
        # do not create any folder!
        #self.logger.debug('Skip creating folder for : %s.' % self.__class__.__name__)
        pass

    @property
    def schema(self):
        project_schema_name = self.ftrack_properties['project_schema']
        project_schema = self.session.query(
            'ProjectSchema where name is "{0}"'.format(project_schema_name)
        ).one()
        # self.logger.info('project_schema: %s' % project_schema)
        return project_schema

    @property
    def task_type(self):
        task_type_name = self.ftrack_properties['task_type']
        task_types = self.schema.get_types('Task')
        filtered_task_types = [task_type for task_type in task_types if task_type['name'] == task_type_name]
        if not filtered_task_types:
            raise FtrackProcessorValidationError(task_types)
        return filtered_task_types[0]

    @property
    def task_status(self):
        try:
            task_statuses = self.schema.get_statuses('Task', self.task_type['id'])
        except ValueError as error:
            raise FtrackProcessorError(error)

        filtered_task_status = [task_status for task_status in task_statuses if task_status['name']]
        # Return first status found.
        return filtered_task_status[0]

    @property
    def shot_status(self):
        shot_statuses = self.schema.get_statuses('Shot')
        filtered_shot_status = [shot_status for shot_status in shot_statuses if shot_status['name']]
        # Return first status found.
        return filtered_shot_status[0]

    @property
    def asset_version_status(self):
        asset_statuses = self.schema.get_statuses('AssetVersion')
        filtered_asset_status = [asset_status for asset_status in asset_statuses if asset_status['name']]
        return filtered_asset_status[0]

    def asset_type_per_task(self, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        try:
            result = self.session.query(
                'AssetType where short is "{0}"'.format(asset_type)
            ).one()
        except Exception as e:
            raise FtrackProcessorError(e)
        return result

    def _create_project_fragment(self, name, parent, task, version):
        project = self.session.query(
            'Project where name is "{0}"'.format(name)
        ).first()
        if not project:
            project = self.session.create('Project', {
                'name': name,
                'full_name': name,
                'project_schema': self.schema
            })
        return project

    def _create_sequence_fragment(self, name, parent, task, version):
        sequence = self.session.query(
            'Sequence where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()
        if not sequence:
            sequence = self.session.create('Sequence', {
                'name': name,
                'parent': parent
            })
        return sequence

    def _create_shot_fragment(self, name, parent, task,version):
        shot = self.session.query(
            'Shot where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()
        if not shot:
            shot = self.session.create('Shot', {
                'name': name,
                'parent': parent,
                'status': self.shot_status
            })
        return shot

    def _create_asset_fragment(self, name, parent, task, version):
        task_name = self.ftrack_properties['task_type']
        ftask = self.session.query(
            'Task where name is "{0}" and parent.id is "{1}"'.format(task_name, parent['id'])
        ).first()

        if not ftask:
            ftask = self.session.create('Task', {
                'name': task_name,
                'parent': parent,
                'status': self.task_status,
                'type': self.task_type
            })

        asset = self.session.query(
            'Asset where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()
        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent':  parent,
                'type': self.asset_type_per_task(task)
            })

        comment = 'Published with: {0} From Nuke Studio : {1}.{2}.{3}'.format(
            self.__class__.__name__, *self.hiero_version_touple
        )

        if not version:
            version = self.session.create('AssetVersion', {
                'asset': asset,
                'status': self.asset_version_status,
                'comment': comment,
                'task': ftask
            })

        return version

    def _create_component_fragment(self, name, parent, task, version):
        component = parent.create_component('/', {
            'name': task._preset.name().lower()
        }, location=None)

        return component

    def _skip_fragment(self, name, parent, task, version):
        self.logger.warning('Skpping: {0}'.format(name))

    def create_project_structure(self, exportItems):
        versions = {}

        for (exportPath, preset) in self._exportTemplate.flatten():
            for item in exportItems:
                self._components.setdefault(item.item().name(), {})

                # Build TaskData seed.
                taskData = hiero.core.TaskData(
                    preset,
                    item,
                    preset.properties()['exportRoot'],
                    exportPath,
                    'v0',
                    self._exportTemplate,
                    item.sequence().project()
                )
                task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

                file_name = '{0}{1}'.format(
                    preset.name().lower(),
                    preset.properties()['ftrack']['component_pattern']
                )
                resolved_file_name = task.resolvePath(file_name)

                path = task.resolvePath(exportPath)
                # self.logger.info('Resolved Path: %s' % path)
                path_id = os.path.dirname(path)
                versions.setdefault(path_id, None)

                parent = None  # After the loop this will be containing the component object.
                for template, token in zip(exportPath.split(os.path.sep), path.split(os.path.sep)):
                    if not versions[path_id] and parent and parent.entity_type == 'AssetVersion':
                        versions[path_id] = parent
                    fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
                    parent = fragment_fn(token, parent, task, versions[path_id])

                self.session.commit()
                # Extract ftrack path from structure and accessors.
                ftrack_shot_path = self.ftrack_location.structure.get_resource_identifier(parent)

                # Ftrack sanitize output path, but we need to retain the original on here
                # otherwise foo.####.ext becomes foo.____.ext
                tokens = ftrack_shot_path.split(os.path.sep)
                tokens[-1] = resolved_file_name
                ftrack_shot_path = os.path.sep.join(tokens)

                ftrack_path = str(os.path.join(self.ftrack_location.accessor.prefix, ftrack_shot_path))

                # self.logger.info('result path: %s' % ftrack_path)
                task._shotPath = ftrack_path
                task._exportPath = ftrack_path
                task._pathid = path_id
                task.setDestinationDescription(ftrack_path)

                self._components[item.item().name()].setdefault(
                    preset.name(),
                    {
                        'component': parent,
                        'path': ftrack_path
                    }
                )

                # tag clips
                self.addFtrackTag(item.item(), task)

    def addFtrackTag(self, originalItem, task):
        localtime = time.localtime(time.time())
        timestamp = self.timeStampString(localtime)

        task_id = str(task._preset.properties()['ftrack']['task_id'])

        data = self._components[originalItem.name()][task._preset.name()]
        component = data['component']

        existingTag = None
        for tag in originalItem.tags():
            if tag.metadata().hasKey('tag.taskid') and tag.metadata()['tag.taskid'] == task_id:
                existingTag = tag
                break

        if existingTag:
            existingTag.metadata().setValue('tag.version_id', component['version']['id'])
            existingTag.metadata().setValue('tag.asset_id', component['version']['asset']['id'])
            existingTag.metadata().setValue('tag.version', str(component['version']['version']))
            self.logger.info('Updating tag: {0}'.format(existingTag))
            # Move the tag to the end of the list.
            originalItem.removeTag(existingTag)
            originalItem.addTag(existingTag)
            return

        tag = hiero.core.Tag(
            task._preset.name(),
            ':/ftrack/image/default/ftrackLogoColor',
            False
        )

        tag.metadata().setValue('tag.taskid', task_id)
        tag.metadata().setValue('tag.component_id', component['id'])
        tag.metadata().setValue('tag.version_id', component['version']['id'])
        tag.metadata().setValue('tag.asset_id', component['version']['asset']['id'])
        tag.metadata().setValue('tag.version', str(component['version']['version']))

        tag.metadata().setValue('tag.description', 'Ftrack Entity')

        self.logger.info('Adding tag: {0} to item {1}'.format(tag, originalItem))
        originalItem.addTag(tag)

    def publishResultComponents(self, render_tasks):
        # all this code should me moved later in a worker

        for render_task in render_tasks:
            render_data = self._components[render_task._item.name()][render_task._preset.name()]
            component = render_data['component']
            publish_path = render_data['path']

            start, end = render_task.outputRange()
            startHandle, endHandle = render_task.outputHandles()

            fps = None
            if render_task._sequence:
                fps = render_task._sequence.framerate().toFloat()

            elif render_task._clip:
                fps = render_task._clip.framerate().toFloat()

            attributes = component['version']['task']['parent']['custom_attributes']

            for attr_name, attr_value in attributes.items():
                if start and attr_name == 'fstart':
                    attributes['fstart'] = str(start)

                if end and attr_name == 'fend':
                    attributes['fend'] = str(end)

                if fps and attr_name == 'fps':
                    attributes['fps'] = str(fps)

                if startHandle and attr_name == 'handles':
                    attributes['handles'] = str(startHandle)

            if '#' in publish_path:
                # todo: Improve this logic
                start, end = render_task.outputRange()
                publish_path = '{0} [{1}-{2}]'.format(publish_path, start, end)

            self.session.create(
                'ComponentLocation', {
                    'location_id': self.ftrack_location['id'],
                    'component_id': component['id'],
                    'resource_identifier': publish_path
                }
            )
            # Add option to publish or not the thumbnail.
            if render_task._preset.properties()['ftrack'].get('opt_publish_thumbnail'):
                self.publishThumbnail(component, render_task)

        self.session.commit()

    def publishThumbnail(self, component, render_task):
        source = render_task._clip.source()
        thumbnail_qimage = source.thumbnail(source.posterFrame())
        thumbnail_file = tempfile.NamedTemporaryFile(prefix='hiero_ftrack_thumbnail', suffix='.png', delete=False).name
        thumbnail_qimage_resized = thumbnail_qimage.scaledToWidth(600, QtCore.Qt.SmoothTransformation)
        thumbnail_qimage_resized.save(thumbnail_file)
        version = component['version']
        version.create_thumbnail(thumbnail_file)
        version['task'].create_thumbnail(thumbnail_file)


    def validateFtrackProcessing(self, exportItems):

        attributes = [
            'task_type',
        ]

        sequences = [item.sequence() for item in exportItems]
        project = sequences[0].project()
        processor_schema = self._preset.properties()['ftrack']['project_schema']
        export_root = self._exportTemplate.exportRootPath()
        errors = {}
        missing_assets_type = []

        for item in exportItems:
            for (exportPath, preset) in self._exportTemplate.flatten():
                # propagate schema from processor to tasks.
                preset.properties()['ftrack']['project_schema'] = processor_schema

                asset_type_code = preset.properties()['ftrack']['asset_type_code']

                ftrack_asset_type = self.session.query(
                    'AssetType where short is "{0}"'.format(asset_type_code)
                ).first()

                if not ftrack_asset_type:
                    missing_assets_type.append(asset_type_code)

                # Build TaskData seed.
                taskData = hiero.core.TaskData(
                    preset,
                    item,
                    export_root,
                    exportPath,
                    'v0',
                    self._exportTemplate,
                    project
                )
                task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)
                for attribute in attributes:
                    try:
                        result = getattr(task, attribute)
                    except FtrackProcessorValidationError as error:
                        valid_values = [result['name'] for result in error.message]
                        preset_errors = errors.setdefault(preset, {})
                        preset_errors.setdefault(attribute, valid_values)

        if errors or missing_assets_type:
            settings_validator = FtrackSettingsValidator(self.session, errors, missing_assets_type)

            if settings_validator.exec_() != QtWidgets.QDialog.Accepted:
                return False

            self.validateFtrackProcessing(exportItems)

        return True


class FtrackProcessorUI(FtrackBase):
    def __init__(self, preset):
        super(FtrackProcessorUI, self).__init__(preset)
        self._nodeSelectionWidget = None

    def addFtrackTaskUI(self, widget, exportTemplate):
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Options (ftrack)')

        # Thumbanil generation.
        key, value, label = 'opt_publish_thumbnail', True, 'Publish Thumbnail'
        thumbnail_tooltip = 'Generate and upload thumbnail'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=thumbnail_tooltip
        )
        form_layout.addRow(label + ':', uiProperty)

        # Component Name.
        key, value, label = 'component_name', '', 'Component Name'
        component_tooltip = 'Set Component Name'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=component_tooltip
        )
        form_layout.addRow(label + ':', uiProperty)

        # Task Type.
        key, value, label = 'task_type', '', 'Task Type'
        component_tooltip = 'View Task Type'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=component_tooltip
        )
        uiProperty.setDisabled(True)
        form_layout.addRow(label + ':', uiProperty)

        # Asset Type.
        key, value, label = 'asset_type_code', '', 'Asset Type'
        component_tooltip = 'View Asset Type'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=component_tooltip
        )
        uiProperty.setDisabled(True)
        form_layout.addRow(label + ':', uiProperty)

        return form_layout

    def addFtrackProcessorUI(self, widget, exportTemplate):

        project_name = self._project.name()
        project = self.session.query(
            'select project_schema.name from Project where name is "{0}"'.format(project_name)
        ).first()

        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')

        schemas = self.session.query('ProjectSchema').all()
        schemas_name = [schema['name'] for schema in schemas]

        key, value, label = 'project_schema', schemas_name, 'Project Schema'
        thumbnail_tooltip = 'Select project schema.'

        schema_property = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=thumbnail_tooltip
        )
        form_layout.addRow(label + ':', schema_property)

        if project:
            # If a project exist , disable the widget and set the previous schema found.
            schema_index = schema_property._widget.findText(project['project_schema']['name'])
            schema_property._widget.setCurrentIndex(schema_index)
            schema_property.setDisabled(True)

        # Hide project path selector Foundry ticket : #36074
        for widget in self._exportStructureViewer.findChildren(QtWidgets.QWidget):
            if (
                    (isinstance(widget, QtWidgets.QLabel) and widget.text() == 'Export To:') or
                    widget.toolTip() == 'Export root path'
            ):
                widget.hide()

            if (isinstance(widget, QtWidgets.QLabel) and widget.text() == 'Export Structure:'):
                widget.hide()
