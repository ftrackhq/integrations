# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import time
import tempfile
import logging
import foundry.ui

import hiero.core

from QtExt import QtCore, QtWidgets, QtGui

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory
from hiero.core.FnExporterBase import TaskCallbacks
from hiero.exporters.FnTimelineProcessor import TimelineProcessor
from hiero.exporters.FnShotProcessor import getShotNameIndex

from ftrack_connect_nuke_studio_beta.processors.ftrack_base import (
    FtrackBasePreset,
    FtrackBase,
    FtrackProcessorValidationError,
    FtrackProcessorError
)
from ftrack_connect_nuke_studio_beta.ui.widget.template import Template
import ftrack_connect_nuke_studio_beta.template as template_manager
from ftrack_connect_nuke_studio_beta.processors.ftrack_base import (
    get_reference_ftrack_project, set_reference_ftrack_project,
    lock_reference_ftrack_project, remove_reference_ftrack_project
)
import ftrack_connect_nuke_studio_beta.exception


class FtrackSettingsValidator(QtWidgets.QDialog):
    '''Settings validation Dialog.'''

    def __init__(self, session, error_data, missing_assets_types):
        '''Return a validator widget for the given *error_data* and *missing_assets_types*.'''
        super(FtrackSettingsValidator, self).__init__()

        self.setWindowTitle('Validation error')
        self._session = session

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        ftrack_icon = QtGui.QIcon(':/ftrack/image/default/ftrackLogoLight')
        self.setWindowIcon(ftrack_icon)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        box = QtWidgets.QGroupBox('An error occured in the current schema configuration.')

        self.layout().addWidget(box)

        box_layout = QtWidgets.QVBoxLayout()
        box.setLayout(box_layout)

        form_layout = TaskUIFormLayout()
        box_layout.addLayout(form_layout)

        template_manager.get_project_template()

        for processor, values in error_data.items():
            form_layout.addDivider('Wrong {0} presets'.format(processor.__class__.__name__))

            for attribute, valid_values in values.items():
                valid_values.insert(0, '- select a value -')
                key, value, label = attribute, valid_values, ' '.join(attribute.split('_'))
                tooltip = 'Set {0} value'.format(attribute)

                uiProperty = UIPropertyFactory.create(
                    type(value),
                    key=key,
                    value=value,
                    dictionary=processor._preset.properties()['ftrack'],
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
                form_layout.addRow('Create asset: ', create_asset_button)

        buttons = QtWidgets.QDialogButtonBox()
        buttons.setOrientation(QtCore.Qt.Horizontal)
        buttons.addButton('Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        buttons.addButton('Accept', QtWidgets.QDialogButtonBox.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)

    def create_missing_asset(self):
        '''Trigger creation of missing assets.'''
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
    '''Base Processor/task preset.'''

    def __init__(self, name, properties):
        '''Initialise with *preset* and *properties*.'''
        super(FtrackProcessorPreset, self).__init__(name, properties)

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for processor.'''
        super(FtrackProcessorPreset, self).set_ftrack_properties(properties)


class FtrackProcessor(FtrackBase):
    '''Base Processor/task.'''

    def __init__(self, initDict):
        '''Initialise base processor with *initDict* .'''

        super(FtrackProcessor, self).__init__(initDict)

        # Store a reference of the origial initialization data.
        self._init_dict = initDict

        # Store a reference of the ftrack properties for easier access.
        self.ftrack_properties = self._preset.properties()['ftrack']

        # Note we do resolve {ftrack_version} as part of the {ftrack_asset} function.
        self.fn_mapping = {
            '{ftrack_project}': self._create_project_fragment,
            '{ftrack_context}': self._create_context_fragment,
            '{ftrack_asset}': self._create_asset_fragment,
            '{ftrack_version}': self._create_version_fragment,
            '{ftrack_component}': self._create_component_fragment
        }
        # these events gets emitted during taskStart and taskFinish
        TaskCallbacks.addCallback(TaskCallbacks.onTaskStart, self.setup_export_paths_event)
        TaskCallbacks.addCallback(TaskCallbacks.onTaskFinish, self.publish_result_component_event)
        # progress for project creation
        self._create_project_progress_widget = None
        self._validate_project_progress_widget = None

    def schema(self, project):
        ''' Return the current ftrack project schema. '''
        project_id, is_locked = get_reference_ftrack_project(project)
        query = 'select project_schema from Project where id is "{0}"'.format(project_id)
        project_entity = self.session.query(query).one()
        return project_entity['project_schema']

    def task_type(self, project):
        ''' Return the ftrack object for the task type set.'''
        task_type_name = self.ftrack_properties['task_type']
        task_types = self.schema(project).get_types('Task')
        filtered_task_types = [task_type for task_type in task_types if task_type['name'] == task_type_name]
        if not filtered_task_types:
            raise FtrackProcessorValidationError(task_types)
        self.logger.info('task_type : {}'.format(filtered_task_types))
        return filtered_task_types[0]

    def task_status(self, project):
        ''' Return the ftrack object for the task status. '''
        try:
            task_statuses = self.schema(project).get_statuses('Task', self.task_type(project)['id'])
        except ValueError as error:
            raise FtrackProcessorError(error)

        filtered_task_status = [task_status for task_status in task_statuses if task_status['name']]
        # Return first status found.
        self.logger.info('task_status : {}'.format(filtered_task_status))
        return filtered_task_status[0]

    def shot_status(self, project):
        '''Return the ftrack object for the shot status.'''
        shot_statuses = self.schema(project).get_statuses('Shot')
        filtered_shot_status = [shot_status for shot_status in shot_statuses if shot_status['name']]
        # Return first status found.
        return filtered_shot_status[0]

    def asset_version_status(self, project):
        '''Return the ftrack object for the asset version status.'''
        asset_statuses = self.schema(project).get_statuses('AssetVersion')
        filtered_asset_status = [asset_status for asset_status in asset_statuses if asset_status['name']]
        return filtered_asset_status[0]

    def asset_type_per_task(self, task):
        '''Return the ftrack object available asset type.'''
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        try:
            result = self.session.query(
                'AssetType where short is "{0}"'.format(asset_type)
            ).one()
        except Exception as error:
            raise FtrackProcessorError(error)
        return result

    def _create_project_fragment(self, name, parent, task, version):
        '''Return ftrack project entity from *name*, *parent*, *task* and *version*.'''
        self.logger.debug('Creating project fragment: {} {} {} {}'.format(name, parent, task, version))

        project = self.session.query(
            'Project where full_name is "{0}"'.format(name)
        ).first()
        if not project:
            project = self.session.create('Project', {
                'name': name,
                'full_name': name,
                'project_schema': self.schema(task._project)
            })

        return project

    def _create_context_fragment(self, composed_name, parent, task, version):
        '''Return ftrack context entity from *composed_name*, *parent*, *task* and *version*.'''
        self.logger.debug('Creating context fragment: {} {} {} {}'.format(composed_name, parent, task, version))
        splitted_name = composed_name.split('|')
        parsed_names = []

        for raw_name in splitted_name:
            object_type, object_name = raw_name.split(':')
            parsed_names.append((object_type, object_name))

        parent = parent

        for object_type, object_name in parsed_names:
            # check if the object_type already exists:

            ftrack_type = self.session.query(
                '{0} where name is "{1}" and parent.id is "{2}"'.format(object_type, object_name, parent['id'])
            ).first()

            if not ftrack_type:
                ftrack_type = self.session.create(object_type, {
                    'name': object_name,
                    'parent': parent,
                })

            parent = ftrack_type

        return parent

    def _create_asset_fragment(self, name, parent, task, version):
        '''Return ftrack asset entity from *name*, *parent*, *task* and *version*.'''
        self.logger.debug('Creating asset fragment: {} {} {} {}'.format(name, parent, task, version))

        asset = self.session.query(
            'Asset where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()

        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent':  parent,
                'type': self.asset_type_per_task(task)
            })

        return asset

    def _create_version_fragment(self, name, parent, task, version):
        '''Return ftrack asset version entity from *name*, *parent*, *task* and *version*.'''
        self.logger.debug('Creating version fragment: {} {} {} {}'.format(name, parent, task, version))

        task_name = self.ftrack_properties['task_type']
        ftask = self.session.query(
            'Task where name is "{0}" and parent.id is "{1}"'.format(task_name, parent['parent']['id'])
        ).first()

        if not ftask:
            ftask = self.session.create('Task', {
                'name': task_name,
                'parent': parent['parent'],
                'status': self.task_status(task._project),
                'type': self.task_type(task._project)
            })

        if not version:
            comment = 'Published with: {0} From Nuke Studio : {1}.{2}.{3}'.format(
                self.__class__.__name__, *self.hiero_version_touple
            )
            version = self.session.create('AssetVersion', {
                'asset': parent,
                'status': self.asset_version_status(task._project),
                'comment': comment,
                'task': ftask
            })

        return version

    def _create_component_fragment(self, name, parent, task, version):
        '''Return ftrack component entity from *name*, *parent*, *task* and *version*.'''
        self.logger.debug('Creating component fragment: {} {} {} {}'.format(name, parent, task, version))

        component = parent.create_component('/', {
            'name': task._preset.name().lower()
        }, location=None)

        return component

    def _skip_fragment(self, name, parent, task, version):
        '''Fallback function if the given fragment *name* is not found.'''
        self.logger.warning('Skpping: {0}'.format(name))

    def _create_extra_tasks(self, task_type_names, task, component):
        '''Create extra tasks based on dropped ftrack tags from *task_type_names* and *component*, '''
        parent = component['version']['asset']['parent']  # Get Shot from component
        task_types = self.schema(task._project).get_types('Task')

        for task_type_name in task_type_names:
            filtered_task_types = [task_type for task_type in task_types if task_type['name'] == task_type_name]
            if len(filtered_task_types) != 1:
                self.logger.debug(
                    'Skipping {0} as is not a valid task type for schema {1}'.format(
                        task_type_name, self.schema(task._project)['name'])
                )
                continue

            task_status = self.schema(task._project).get_statuses('Task', filtered_task_types[0]['id'])

            ftask = self.session.query(
                'Task where name is "{0}" and parent.id is "{1}"'.format(task_type_name, parent['id'])
            ).first()

            if not ftask:
                self.session.create('Task', {
                    'name': task_type_name,
                    'parent': parent,
                    'status': task_status[0],
                    'type': filtered_task_types[0]
                })

        self.session.commit()

    def create_project_structure(self, export_items):
        '''Create project structure on ftrack server given *export_items*.

        Return list of filtered *export_items*.

        '''
        filtered_export_items = []
        self._create_project_progress_widget = foundry.ui.ProgressTask('Creating structure in ftrack...')
        progress_index = 0
        # ensure to reset components before creating a new project.
        self._components = {}
        versions = {}
        project = export_items[0].item().project()
        parsing_template = template_manager.get_project_template(project)

        num_items = len(self._exportTemplate.flatten()) * len(export_items)
        for export_item in export_items:
            track_item = export_item.item()

            # Skip effects track items.
            if isinstance(track_item, hiero.core.EffectTrackItem):
                self.logger.debug('Skipping {0}'.format(track_item))
                continue

            try:
                template_manager.match(track_item, parsing_template)
            except ftrack_connect_nuke_studio_beta.exception.TemplateError:
                self.logger.warning(
                    'Skipping {} as does not match {}'.format(track_item, parsing_template['expression']))
                continue

            filtered_export_items.append(export_item)

            for (exportPath, preset) in self._exportTemplate.flatten():

                progress_index += 1
                self._create_project_progress_widget.setProgress(int(100.0 * (float(progress_index) / float(num_items))))

                # collect task tags per clip
                task_tags = set()

                if not hasattr(track_item, 'tags'):
                    continue

                for tag in track_item.tags():
                    meta = tag.metadata()
                    if meta.hasKey('type') and meta.value('type') == 'ftrack':
                        task_name = meta.value('ftrack.name')
                        task_tags.add(task_name)

                shot_name_index = getShotNameIndex(track_item)
                if isinstance(self, TimelineProcessor):
                    track_item = export_item.item().sequence()
                    shot_name_index = ''

                # create entry points on where to store ftrack component and path data.
                self._components.setdefault(track_item.name(), {})
                self._components[track_item.name()].setdefault(preset.name(), {})

                retime = self._preset.properties().get('includeRetimes', False)

                cut_handles = None
                start_frame = None

                if self._preset.properties()['startFrameSource'] == 'Custom':
                    start_frame = self._preset.properties()['startFrameIndex']

                # If we are exporting the shot using the cut length (rather than the (shared) clip length)
                if self._preset.properties().get('cutLength'):
                    # Either use the specified number of handles or zero
                    if self._preset.properties().get('cutUseHandles'):
                        cut_handles = int(self._preset.properties()['cutHandles'])
                    else:
                        cut_handles = 0

                # Build TaskData seed
                taskData = hiero.core.TaskData(
                    preset,
                    track_item,
                    preset.properties()['exportRoot'],
                    exportPath,
                    'v0',
                   self._exportTemplate,
                   project=track_item.project(),
                   cutHandles=cut_handles,
                   retime=retime,
                   startFrame=start_frame,
                   startFrameSource=self._preset.properties()['startFrameSource'],
                   resolver=self._preset.createResolver(),
                   submission=self._submission,
                   skipOffline=self.skipOffline(),
                   presetId=hiero.core.taskRegistry.addPresetToProjectExportHistory(track_item.project(), self._preset),
                   shotNameIndex=shot_name_index
                )

                task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

                file_name = '{0}{1}'.format(
                    preset.name().lower(),
                    preset.properties()['ftrack']['component_pattern']
                )
                resolved_file_name = task.resolvePath(file_name)

                path = task.resolvePath(exportPath)
                path_id = os.path.dirname(path)
                versions.setdefault(path_id, None)

                parent = None  # After the loop this will be containing the component object.
                for template, token in zip(exportPath.split(self.path_separator), path.split(self.path_separator)):
                    if not versions[path_id] and parent and parent.entity_type == 'AssetVersion':
                        versions[path_id] = parent

                    fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
                    parent = fragment_fn(token, parent, task, versions[path_id])

                self.session.commit()
                self._create_extra_tasks(task_tags, task, parent)

                # Extract ftrack path from structure and accessors.
                ftrack_shot_path = self.ftrack_location.structure.get_resource_identifier(parent)

                # Ftrack sanitize output path, but we need to retain the original on here
                # otherwise foo.####.ext becomes foo.____.ext
                tokens = ftrack_shot_path.split(self.path_separator)

                tokens[-1] = resolved_file_name
                ftrack_shot_path = self.path_separator.join(tokens)

                ftrack_path = str(os.path.join(self.ftrack_location.accessor.prefix, ftrack_shot_path))

                data = {
                    'component': parent,
                    'path': ftrack_path,
                    'published': False
                }

                self._components[track_item.name()][preset.name()] = data
                self.add_ftrack_tag(track_item, task)

        # we have successfully exported the project, so now we can lock it.
        lock_reference_ftrack_project(project)

        self._create_project_progress_widget = None
        return filtered_export_items

    def add_ftrack_tag(self, original_item, task):
        ''' Add ftrack tag to *original_item* for *task*. '''
        if not hasattr(original_item, 'tags'):
            return

        item = task._item

        localtime = time.localtime(time.time())

        start, end = task.outputRange(clampToSource=False)
        start_handle, end_handle = task.outputHandles()

        task_id = str(task._preset.properties()['ftrack']['task_id'])

        data = self._components[original_item.name()][task._preset.name()]
        component = data['component']

        path = data['path']
        frame_offset = start if start else 0

        collate = getattr(task, '_collate', False)
        applying_retime = (task._retime and task._cutHandles is not None) or collate
        applied_retimes_str = '1' if applying_retime else '0'

        existing_tag = None
        for tag in original_item.tags():
            if tag.metadata().hasKey('tag.presetid') and tag.metadata()['tag.presetid'] == task_id:
                existing_tag = tag
                break

        if existing_tag:
            existing_tag.metadata().setValue('tag.version_id', component['version']['id'])
            existing_tag.metadata().setValue('tag.asset_id', component['version']['asset']['id'])
            existing_tag.metadata().setValue('tag.version', str(component['version']['version']))
            existing_tag.metadata().setValue('tag.path', path)
            existing_tag.metadata().setValue('tag.pathtemplate', task._exportPath)

            existing_tag.metadata().setValue('tag.startframe', str(start))
            existing_tag.metadata().setValue('tag.duration', str(end - start+1))
            existing_tag.metadata().setValue('tag.starthandle', str(start_handle))
            existing_tag.metadata().setValue('tag.endhandle', str(end_handle))
            existing_tag.metadata().setValue('tag.frameoffset', str(frame_offset))
            existing_tag.metadata().setValue('tag.localtime', str(localtime))
            existing_tag.metadata().setValue('tag.appliedretimes', applied_retimes_str)

            if task._preset.properties().get('keepNukeScript'):
                existing_tag.metadata().setValue('tag.script', task.resolvedExportPath())

            if task._cutHandles:
                existing_tag.metadata().setValue('tag.handles', str(task._cutHandles))

            if isinstance(item, hiero.core.TrackItem):
                existing_tag.metadata().setValue('tag.sourceretime', str(item.playbackSpeed()))

            original_item.removeTag(existing_tag)
            original_item.addTag(existing_tag)
            return

        tag = hiero.core.Tag(
            '{0}'.format(task._preset.name()),
            ':/ftrack/image/default/ftrackLogoLight',
            False
        )
        tag.metadata().setValue('tag.provider', 'ftrack')

        tag.metadata().setValue('tag.presetid', task_id)
        tag.metadata().setValue('tag.component_id', component['id'])
        tag.metadata().setValue('tag.version_id', component['version']['id'])
        tag.metadata().setValue('tag.asset_id', component['version']['asset']['id'])
        tag.metadata().setValue('tag.version', str(component['version']['version']))
        tag.metadata().setValue('tag.path', path)
        tag.metadata().setValue('tag.description', 'ftrack {0}'.format(task._preset.name()))

        tag.metadata().setValue('tag.pathtemplate', task._exportPath)

        tag.metadata().setValue('tag.startframe', str(start))
        tag.metadata().setValue('tag.duration', str(end - start+1))
        tag.metadata().setValue('tag.starthandle', str(start_handle))
        tag.metadata().setValue('tag.endhandle', str(end_handle))
        tag.metadata().setValue('tag.frameoffset', str(frame_offset))
        tag.metadata().setValue('tag.localtime', str(localtime))
        tag.metadata().setValue('tag.appliedretimes', applied_retimes_str)

        if task._preset.properties().get('keepNukeScript'):
            tag.metadata().setValue('tag.script', task.resolvedExportPath())

        if task._cutHandles:
            tag.metadata().setValue('tag.handles', str(task._cutHandles))

        if isinstance(item, hiero.core.TrackItem):
            tag.metadata().setValue('tag.sourceretime', str(item.playbackSpeed()))

        original_item.addTag(tag)

    def setup_export_paths_event(self, task):
        ''' Event spawned when *task* start. '''
        has_data = self._components.get(
            task._item.name(), {}
        ).get(task._preset.name())

        if not has_data:
            return

        render_data = has_data

        output_path = render_data['path']
        task._exportPath = output_path
        task.setDestinationDescription(output_path)

        def _makeNullPath():
            pass

        task._makePath = _makeNullPath

    def publish_result_component_event(self, render_task):
        ''' Event spawned when *render_task* frame is rendered. '''
        has_data = self._components.get(
            render_task._item.name(), {}
        ).get(render_task._preset.name())

        if not has_data:
            return

        render_data = has_data

        component = render_data['component']
        publish_path = render_data['path']
        is_published = render_data['published']

        if render_task.error():
            self.logger.warning('An Error occurred while rendering: {0}'.format(publish_path))
            return

        if is_published:
            return

        start, end = render_task.outputRange(clampToSource=False)
        start_handle, end_handle = render_task.outputHandles()

        fps = None
        if render_task._sequence:
            fps = render_task._sequence.framerate().toFloat()

        elif render_task._clip:
            fps = render_task._clip.framerate().toFloat()

        parent = component['version']['task']['parent']

        attributes = parent['custom_attributes']

        for attr_name, attr_value in attributes.items():
            if start and attr_name == 'fstart':
                attributes['fstart'] = str(start)

            if end and attr_name == 'fend':
                attributes['fend'] = str(end)

            if fps and attr_name == 'fps':
                attributes['fps'] = str(fps)

            if start_handle and attr_name == 'handles':
                attributes['handles'] = str(start_handle)

        if '#' in publish_path:
            # todo: Improve this logic
            publish_path = '{0} [{1}-{2}]'.format(publish_path, start, end)

        self.session.create(
            'ComponentLocation', {
                'location_id': self.ftrack_location['id'],
                'component_id': component['id'],
                'resource_identifier': publish_path
            }
        )
        self.logger.debug('Publishing : {0}'.format(publish_path))

        # Add option to publish or not the thumbnail.
        if self._preset.properties()['ftrack'].get('opt_publish_thumbnail'):
            self.publish_thumbnail(component, render_task)

        # Add option to publish or not the reviewable.
        if self._preset.properties()['ftrack'].get('opt_publish_reviewable'):
            _, ext = os.path.splitext(publish_path)
            if ext == '.mov':
                component['version'].encode_media(publish_path)

        self.session.commit()
        render_data['published'] = True

    def publish_thumbnail(self, component, render_task):
        ''' Generate thumbnail *component* for *render_task*. '''
        source = render_task._clip
        thumbnail_qimage = source.thumbnail(source.posterFrame())
        thumbnail_file = tempfile.NamedTemporaryFile(prefix='hiero_ftrack_thumbnail', suffix='.png', delete=False).name
        thumbnail_qimage_resized = thumbnail_qimage.scaledToWidth(1280, QtCore.Qt.SmoothTransformation)
        thumbnail_qimage_resized.save(thumbnail_file)
        version = component['version']
        version.create_thumbnail(thumbnail_file)
        version['task'].create_thumbnail(thumbnail_file)

    def validate_ftrack_processing(self, export_items, preview):
        ''' Return whether the *export_items* and processor are valid to be rendered.

        In *preview* will not go through the whole validation, and return False by default.

        '''
        project = export_items[0].item().project()
        parsing_template = template_manager.get_project_template(project)
        task_tags = set()
        task_types = self.schema(project).get_types('Task')

        task_type = self._preset.properties()['ftrack']['task_type']
        asset_type_code = self._preset.properties()['ftrack']['asset_type_code']
        asset_name = self._preset.properties()['ftrack']['asset_name']

        for (export_path, preset) in self._exportTemplate.flatten():
            # propagate properties from processor to tasks.
            preset.properties()['ftrack']['task_type'] = task_type
            preset.properties()['ftrack']['asset_type_code'] = asset_type_code
            preset.properties()['ftrack']['asset_name'] = asset_name

        if preview:
            return False
        else:
            self._validate_project_progress_widget = foundry.ui.ProgressTask('Validating settings.')
            errors = {}
            missing_assets_type = []
            non_matching_template_items = []

            num_items = len(self._exportTemplate.flatten()) + len(export_items)
            progress_index = 0
            for exportItem in export_items:

                item = exportItem.item()

                # Skip effects track items.
                if isinstance(item, hiero.core.EffectTrackItem):
                    self.logger.debug('Skipping {0}'.format(exportItem))
                    continue

                try:
                    template_manager.match(item, parsing_template)
                except ftrack_connect_nuke_studio_beta.exception.TemplateError:
                    self.logger.warning('Skipping {} as does not match {}'.format(item, parsing_template['expression']))
                    if item not in non_matching_template_items:
                        non_matching_template_items.append(item.name())
                    continue

                if not hasattr(item, 'tags'):
                    continue

                for tag in item.tags():
                    meta = tag.metadata()
                    if meta.hasKey('type') and meta.value('type') == 'ftrack':
                        task_name = meta.value('ftrack.name')
                        filtered_task_types = [task_type for task_type in task_types if task_type['name'] == task_name]
                        if len(filtered_task_types) == 1:
                            task_tags.add(task_name)

                for (export_path, preset) in self._exportTemplate.flatten():
                    progress_index += 1
                    self._validate_project_progress_widget.setProgress(int(100.0 * (float(progress_index) / float(num_items))))
                    asset_type_code = preset.properties()['ftrack']['asset_type_code']

                    ftrack_asset_type = self.session.query(
                        'AssetType where short is "{0}"'.format(asset_type_code)
                    ).first()

                    if not ftrack_asset_type and asset_type_code not in missing_assets_type:
                        missing_assets_type.append(asset_type_code)

                    try:
                        result = self.task_type(project)
                    except FtrackProcessorValidationError as error:
                        preset_errors = errors.setdefault(self, {})
                        preset_errors.setdefault('task_type', list(task_tags))

            self._validate_project_progress_widget = None

            self.logger.info(errors)

            # raise validation window
            if errors or missing_assets_type:
                settings_validator = FtrackSettingsValidator(self.session, errors, missing_assets_type)

                if settings_validator.exec_() != QtWidgets.QDialog.Accepted:
                    return False

                self.validate_ftrack_processing(export_items)

            # raise notification for error parsing items
            if non_matching_template_items:
                item_warning = QtWidgets.QMessageBox().warning(
                    None,
                    'Error parsing Track Items',
                    'Some items failed to parse and will not be published\n'
                    '{} do you want to continue with the others ?'.format(', '.join(non_matching_template_items)),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if item_warning != QtWidgets.QMessageBox.Yes:
                    return False
                else:
                    # user has been notified, and want to go ahead....
                    non_matching_template_items = []

            return True


class FtrackProcessorUI(FtrackBase):
    '''Base processor/task Ui.'''

    def __init__(self, preset):
        '''Initialise with *preset*.'''
        super(FtrackProcessorUI, self).__init__(preset)
        self._nodeSelectionWidget = None

        # Variable placeholders for ui fragments.
        self.project_options_widget = None
        self.schema_options_widget = None
        self.task_type_options_widget = None
        self.asset_name_options_widget = None
        self.thumbnail_options_widget = None
        self.reviewable_options_widget = None
        self.asset_type_options_widget = None
        self.template_widget_options_widget = None

    def add_project_options(self, parent_layout):
        '''Create project options widget with parent *parent_layout*.'''

        ftrack_projects = self.session.query(
            'select id, name from Project where status is "active"'
        ).all()

        project_names = [project['full_name'] for project in ftrack_projects]
        key, value, label = 'project_name', project_names, 'Create under Project'
        tooltip = 'Updating/Creating Project.'

        self.project_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary={},
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.project_options_widget)

        # Update project tag on changes
        self.project_options_widget._widget.currentIndexChanged.connect(self._set_project_tag)

        # check if the project is be locked
        project_id_tag, project_is_locked = get_reference_ftrack_project(self._project)
        if project_is_locked and project_id_tag:
            project = self.session.get('Project', project_id_tag)
            if not project:
                self.logger.warning('Project id {} found, but project does not exist on server!'.format(project_id_tag))
                remove_reference_ftrack_project(self._project)
                return

            project_name = project['full_name']
            self.logger.info('Found Project id tag, locking project to : {}'.format(project_name))
            project_index = self.project_options_widget._widget.findText(project_name)
            self.project_options_widget._widget.setCurrentIndex(project_index)
            self.project_options_widget.setDisabled(True)

        else:
            # force event emission
            current_index = self.project_options_widget._widget.currentIndex()
            self.project_options_widget._widget.currentIndexChanged.emit(current_index)

    def _set_project_tag(self):
        project_name = self.project_options_widget._widget.currentText()
        ftrack_project = self.session.query('Project where full_name is "{}"'.format(project_name)).one()
        set_reference_ftrack_project(self._project, ftrack_project['id'])

    def add_task_type_options(self, parent_layout, export_items):
        '''Create task type options widget for *export_items* with parent *parent_layout*.'''
        # provide access to tags.
        task_tags = set()
        for exportItem in export_items:
            item = exportItem.item()
            if not hasattr(item, 'tags'):
                continue

            for tag in item.tags():
                meta = tag.metadata()
                if meta.hasKey('type') and meta.value('type') == 'ftrack':
                    task_name = meta.value('ftrack.name')
                    task_tags.add(task_name)

        task_tags = list(task_tags) or [self._preset.properties()['ftrack']['task_type']]
        key, value, label = 'task_type', list(task_tags), 'Publish to Task'
        tooltip = 'Select a task to publish to.'

        self.task_type_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.task_type_options_widget)

    def add_asset_name_options(self, parent_layout):
        '''Create asset name options widget with parent *parent_layout*.'''
        asset_name = self._preset.properties()['ftrack']['asset_name']
        key, value, label = 'asset_name', asset_name, 'Set asset name as'
        tooltip = 'Select an asset name to publish to.'
        self.asset_name_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.asset_name_options_widget)

    def add_thumbnail_options(self, parent_layout):
        '''Create thumbnail options widget with parent *parent_layout*.'''
        # Thumbanil generation.
        key, value, label = 'opt_publish_thumbnail', True, 'Publish Thumbnail'
        tooltip = 'Generate and upload thumbnail'

        self.thumbnail_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.thumbnail_options_widget)

    def add_reviewable_options(self, parent_layout):
        '''Create reviewable options widget with parent *parent_layout*.'''
        key, value, label = 'opt_publish_reviewable', True, 'Publish Reviewable'
        tooltip = 'Upload reviewable'

        self.reviewable_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.reviewable_options_widget)

    def add_asset_type_options(self, parent_layout):
        '''Create asset type options widget with parent *parent_layout*.'''
        asset_types = self.session.query(
            'AssetType'
        ).all()

        asset_type_names = [asset_type['short'] for asset_type in asset_types]
        key, value, label = 'asset_type_code', asset_type_names, 'Asset Type'
        tooltip = 'Asset type to be created.'

        self.asset_type_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', self.asset_type_options_widget)

    def add_task_templates_options(self, parent_layout):
        ''' Create task template options widget with parent *parent_layout*.'''
        self.template_widget_options_widget = Template(self._project)
        parent_layout.addRow('Shot Template' + ':', self.template_widget_options_widget)

    def set_ui_tweaks(self):
        ''' Utility function to tweak NS ui.'''
        # Hide project path selector Foundry ticket : #36074
        for widget in self._exportStructureViewer.findChildren(QtWidgets.QWidget):
            if (
                    (isinstance(widget, QtWidgets.QLabel) and widget.text() == 'Export To:') or
                    widget.toolTip() == 'Export root path'
            ):
                widget.hide()

            if (isinstance(widget, QtWidgets.QLabel) and widget.text() == 'Export Structure:'):
                widget.hide()

    def addFtrackProcessorUI(self, widget, export_items):
        '''Add custom ftrack widgets to parent *widget* for given *export_items*.'''
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')
        self.add_task_templates_options(form_layout)
        self.add_project_options(form_layout)
        self.add_task_type_options(form_layout, export_items)
        self.add_asset_type_options(form_layout)
        self.add_asset_name_options(form_layout)
        self.add_thumbnail_options(form_layout)
        self.add_reviewable_options(form_layout)
        self.set_ui_tweaks()

