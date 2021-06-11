# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import re
import os
import time
import clique
import tempfile
import logging
import foundry.ui
import uuid
import hiero.core
from Qt import QtWidgets, QtCore, QtGui


from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory
from hiero.core.FnExporterBase import TaskCallbacks
from hiero.exporters.FnTimelineProcessor import TimelineProcessor
from hiero.exporters.FnShotProcessor import getShotNameIndex

from ftrack_connect_nuke_studio.processors.ftrack_base import (
    FtrackBasePreset,
    FtrackBase,
    FtrackProcessorValidationError,
    FtrackProcessorError
)
from ftrack_connect_nuke_studio.ui.widget.template import Template
import ftrack_connect_nuke_studio.template as template_manager
import ftrack_connect_nuke_studio.exception
from ftrack_connect_nuke_studio.config import report_exception
from ftrack_connect_nuke_studio import resource


class FtrackSettingsValidator(QtWidgets.QDialog):
    '''Settings validation Dialog.'''

    def __init__(self, session, error_data, missing_assets_types, duplicated_components):
        '''Return a validator widget for the given *error_data* and *missing_assets_types*.'''
        super(FtrackSettingsValidator, self).__init__()

        self.setWindowTitle('Validation error')
        self._session = session

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        ftrack_icon = QtGui.QIcon(QtGui.QPixmap(':/ftrack/image/default/ftrackLogoLight'))
        self.setWindowIcon(ftrack_icon)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        box = QtWidgets.QGroupBox('An error occured in the current schema configuration.')

        self.layout().addWidget(box)

        box_layout = QtWidgets.QVBoxLayout()
        box.setLayout(box_layout)

        form_layout = TaskUIFormLayout()
        box_layout.addLayout(form_layout)
        if duplicated_components:

            form_layout.addDivider(
                '{} Duplicated components name have been found'.format(
                    len(duplicated_components)
                )
            )

            for component_name, task in duplicated_components:

                ui_property = UIPropertyFactory.create(
                    type(component_name),
                    key='component_name',
                    value=component_name,
                    dictionary=task._preset.properties()['ftrack'],
                    label='Component ' + ':',
                    tooltip='Duplicated component name'
                )
                ui_property.update(True)
                form_layout.addRow('Duplicated component' + ':', ui_property)

                if component_name != task.component_name():
                    component_index = duplicated_components.index((task.component_name(), task))
                    duplicated_components.pop(component_index)

        for processor, values in error_data.items():
            form_layout.addDivider('Wrong {0} presets'.format(processor.__class__.__name__))

            for attribute, valid_values in values.items():
                valid_values.insert(0, '- select a value -')
                key, value, label = attribute, valid_values, ' '.join(attribute.split('_'))
                tooltip = 'Set {0} value'.format(attribute)

                ui_property = UIPropertyFactory.create(
                    type(value),
                    key=key,
                    value=value,
                    dictionary=processor._preset.properties()['ftrack'],
                    label=label + ':',
                    tooltip=tooltip
                )
                form_layout.addRow(label + ':', ui_property)
                ui_property.update(True)

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
                'short': asset_type.lower().replace(' ', '_'),
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

        # Note we do resolve {ftrack_version}
        # as part of the {ftrack_asset} function.
        self.fn_mapping = {
            '{ftrack_project_structure}': self._create_projct_structure_fragment,
            '{ftrack_version}': self._create_version_fragment,
            '{ftrack_component}': self._create_component_fragment
        }
        # these events gets emitted during taskStart and taskFinish
        TaskCallbacks.addCallback(
            TaskCallbacks.onTaskStart, self.setup_export_paths_event
        )

        TaskCallbacks.addCallback(
            TaskCallbacks.onTaskFinish, self.publish_result_component_event
        )
        # progress for project creation
        self._create_project_progress_widget = None
        self._validate_project_progress_widget = None

    def schema(self, project):
        ''' Return the current ftrack project schema. '''

        project_id = os.getenv('FTRACK_CONTEXTID')
        project = self.session.get('Project', project_id)

        query = 'select project_schema from Project where id is "{0}"'.format(project['id'])
        project_entity = self.session.query(query).one()
        return project_entity['project_schema']

    def task_type(self, project):
        ''' Return the ftrack object for the task type set.'''
        task_type_name = self.ftrack_properties['task_type']
        task_types = self.schema(project).get_types('Task')
        filtered_task_types = [
            task_type for task_type in task_types if (
                task_type['name'] == task_type_name
            )
        ]
        if not filtered_task_types:
            raise FtrackProcessorValidationError(task_types)
        return filtered_task_types[0]

    def task_status(self, project):
        ''' Return the ftrack object for the task status. '''
        try:
            task_statuses = self.schema(project).get_statuses('Task', self.task_type(project)['id'])
        except ValueError as error:
            raise FtrackProcessorError(error)

        filtered_task_status = [task_status for task_status in task_statuses if task_status['name']]
        # Return first status found.
        return filtered_task_status[0]

    def shot_status(self, project):
        '''Return the ftrack object for the shot status.'''
        shot_statuses = self.schema(project).get_statuses('Shot')
        filtered_shot_status = [
            shot_status for shot_status in shot_statuses if (
                shot_status['name']
            )
        ]
        # Return first status found.
        return filtered_shot_status[0]

    def asset_version_status(self, project):
        '''Return the ftrack object for the asset version status.'''
        asset_statuses = self.schema(project).get_statuses('AssetVersion')
        filtered_asset_status = [
            asset_status for asset_status in asset_statuses if (
                asset_status['name']
            )
        ]
        return filtered_asset_status[0]

    def asset_type_per_task(self, task):
        '''Return the ftrack object available asset type.'''
        asset_type = task._preset.properties()['ftrack']['asset_type_name']
        try:
            result = self.session.query(
                'AssetType where name is "{0}"'.format(asset_type)
            ).first()
        except Exception as error:
            raise FtrackProcessorError(error)
        return result

    def _get_start_end_frame(self, task):
        '''Return start, end frame from given *task*.'''
        start , end = task.outputRange(clampToSource=False)
        self.logger.debug(
            '{2} :: start frame {0}, end frame {1} '.format(
                start, end, task
            )
        )
        return start, end

    def _create_projct_structure_fragment(self, composed_name, parent, task, version):
        '''Return ftrack context entity from *composed_name*, *parent*, *task* and *version*.'''
        self.logger.debug(
            'Creating context fragment: {} {} {} {}'.format(
                composed_name, parent, task, version
            )
        )
        if not composed_name:
            raise Exception(
                'Error with composed_name provided: {}!'.format(
                    composed_name
                )
            )

        splitted_name = composed_name.split('|')

        parsed_names = []

        for raw_name in splitted_name:
            object_type, object_name = raw_name.split(':')
            parsed_names.append((object_type, object_name))

        parent = parent

        for object_type, object_name in parsed_names:
            # Check if the object_type already exists.
            ftrack_type = None

            query = '{0} where name is "{1}"'
            if object_type == 'Project':
                query = '{0} where full_name is "{1}"'

            if parent:
                query += ' and parent.id is "{2}"'
                ftrack_type = self.session.query(
                    query.format(object_type, object_name, parent['id'])
                ).first()
            else:
                # we are dealing with a project
                query += ' and project_schema.id is "{2}"'
                ftrack_type = self.session.query(
                    query.format(object_type, object_name, self.schema(
                        task._project
                    )['id'])
                ).first()

            if not ftrack_type:
                if parent:
                    self.logger.debug(
                        'Creating {} with name {} and parent {}'.format(
                            object_type, object_name, parent
                        )
                    )
                    ftrack_type = self.session.create(object_type, {
                        'name': object_name,
                        'parent': parent,
                    })

            parent = ftrack_type
        return parent

    def _create_version_fragment(self, name, parent, task, version):
        '''Return ftrack asset version entity from *name*, *parent*,
         *task* and *version*.
        '''
        # retrieve asset name from task preset

        resolved_asset_name = task._resolver.resolve(task, self.ftrack_properties['asset_name'])
        asset_name = self.sanitise_for_filesystem(resolved_asset_name)

        self.logger.debug(
            'Creating asset fragment: {} {} {} {}'.format(
                asset_name, parent, task, version
            )
        )

        asset = self.session.query(
            'Asset where name is "{0}" and parent.id is "{1}"'.format(asset_name, parent['id'])
        ).first()

        if not asset:
            asset = self.session.create('Asset', {
                'name': asset_name,
                'parent':  parent,
                'type': self.asset_type_per_task(task)
            })

        self.logger.debug(
            'Creating version fragment: {} {} {} {}'.format(
                name, asset, task, version
            )
        )

        task_name = self.ftrack_properties['task_type']
        ftask = self.session.query(
            'Task where name is "{0}" and parent.id is "{1}"'.format(
                task_name, asset['parent']['id']
            )
        ).first()

        if not ftask:
            ftask = self.session.create('Task', {
                'name': task_name,
                'parent': asset['parent'],
                'status': self.task_status(task._project),
                'type': self.task_type(task._project)
            })

        if not version:
            asset_type_name = self.asset_type_per_task(task)['name']
            context_name = parent['name']
            comment = '“Publish {0} to {1}”'.format(
                asset_type_name, context_name
            )

            version = self.session.create('AssetVersion', {
                'asset': asset,
                'status': self.asset_version_status(task._project),
                'task': ftask,
                'comment': comment
            })

            app_metadata = 'Published with: {0} From Nuke Studio : {1}.{2}.{3}'.format(
                self.__class__.__name__, *self.hiero_version_tuple
            )
            version['metadata']['app_metadata'] = app_metadata

        return version

    def _create_component_fragment(self, name, parent, task, version):
        '''Return ftrack component entity from *name*, *parent*,
         *task* and *version*.
        '''
        self.logger.debug(
            'Creating component fragment: {} {} {} {}'.format(
                name, parent, task, version
            )
        )

        component_name = task.component_name()

        # check if a component with the same name, under the version already exist.
        component = self.session.query('Component where name is "{}" and version.id is "{}"'.format(
            component_name, parent['id']
        )).first()

        if not component:
            is_sequence = re.search(
                '(?<=\.)((%+\d+d)|(#+)|(%d)|(\d+))(?=\.)', name
            )

            if is_sequence:
                start, end = self._get_start_end_frame(task)

                name = '/{} [{}-{}]'.format(name, start, end)

            component = parent.create_component(
                name,
                {
                    'name': component_name
                },
                location=None
            )

            self.logger.info('Component {} created with name {}'.format(component, name))

        return component

    def _skip_fragment(self, name, parent, task, version):
        '''Fallback function if the given fragment *name* is not found.'''
        self.logger.warning('Skpping: {0}'.format(name))

    def _create_extra_tasks(self, task_type_names, task, component):
        '''Create extra tasks based on dropped ftrack tags from
        *task_type_names* and *component*,
        '''
        # Get Shot from component
        parent = component['version']['asset']['parent']
        task_types = self.schema(task._project).get_types('Task')

        for task_type_name in task_type_names:
            filtered_task_types = [
                task_type for task_type in task_types if (
                    task_type['name'] == task_type_name
                )
            ]
            if len(filtered_task_types) != 1:
                self.logger.debug(
                    'Skipping {0} as is not a valid '
                    'task type for schema {1}'.format(
                        task_type_name, self.schema(task._project)['name'])
                )
                continue

            task_status = self.schema(
                task._project
            ).get_statuses('Task', filtered_task_types[0]['id'])

            ftask = self.session.query(
                'Task where name is "{0}" and parent.id is "{1}"'.format(
                    task_type_name, parent['id']
                )
            ).first()

            if not ftask:
                self.session.create('Task', {
                    'name': task_type_name,
                    'parent': parent,
                    'status': task_status[0],
                    'type': filtered_task_types[0]
                })

        self.session.commit()

    @report_exception
    def create_project_structure(self, export_items):
        '''Create project structure on ftrack server given *export_items*.

        Return list of filtered *export_items*.

        '''
        filtered_export_items = []
        self._create_project_progress_widget = foundry.ui.ProgressTask(
            'Creating structure in ftrack...'
        )
        progress_index = 0
        # Ensure to reset components before creating a new project.
        self._components = {}
        versions = {}

        num_items = len(self._exportTemplate.flatten()) * len(export_items)
        for export_item in export_items:
            track_item = export_item.item()

            # Skip effects track items.
            if isinstance(
                    track_item,
                    (hiero.core.EffectTrackItem, hiero.core.Transition)
            ):
                self.logger.debug('Skipping {0}'.format(track_item))
                continue

            project = export_item.item().project()
            parsing_template = template_manager.get_project_template(project)

            try:
                template_manager.match(track_item, parsing_template)
            except ftrack_connect_nuke_studio.exception.TemplateError:
                self.logger.warning(
                    'Skipping {} as does not match {}'.format(
                        track_item, parsing_template['expression']
                    )
                )
                continue

            for (exportPath, preset) in self._exportTemplate.flatten():

                progress_index += 1
                self._create_project_progress_widget.setProgress(
                    int(100.0 * (float(progress_index) / float(num_items)))
                )

                # Collect task tags per clip.
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

                try:
                    root_item = track_item.parentTrack().name()
                except:
                    root_item = track_item.name()

                # Create entry points on where to store ftrack component and path data.
                self._components.setdefault(root_item, {})
                self._components[root_item].setdefault(track_item.name(), {})

                retime = self._preset.properties().get('includeRetimes', False)

                cut_handles = None
                start_frame = None

                if self._preset.properties()['startFrameSource'] == 'Custom':
                    start_frame = self._preset.properties()['startFrameIndex']

                # If we are exporting the shot using the cut length
                # (rather than the (shared) clip length)
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
                    resolver=preset.createResolver(),
                    submission=self._submission,
                    skipOffline=self.skipOffline(),
                    shotNameIndex=shot_name_index
                )

                task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)
                if not task.hasValidItem():
                    continue

                self._components[root_item][track_item.name()].setdefault(task.component_name(), {})

                if getattr(task, '_nothingToDo', False) is True:
                    # Do not create anything if the task is set not to do anything.
                    self.logger.warning('Skipping Task {} is set as disabled'.format(task))
                    continue

                if export_item not in filtered_export_items:
                    self.logger.info('adding {} to filtered export items'.format(export_item))
                    filtered_export_items.append(export_item)

                file_name = '{0}{1}'.format(
                    task.component_name(),
                    preset.properties()['ftrack']['component_pattern']
                ).lower()

                path = task.resolvePath(exportPath)
                path_id = os.path.dirname(path)

                versions.setdefault(path_id, None)

                # After the loop this will be containing the component object.
                zipped_path_separator = zip(
                    exportPath.split(self.path_separator),
                    path.split(self.path_separator)
                )
                parent = None

                for template, token in zipped_path_separator:
                    if (
                            not versions[path_id] and
                            parent and
                            parent.entity_type == 'AssetVersion'
                    ):
                        versions[path_id] = parent

                    fragment_fn = self.fn_mapping.get(
                        template, self._skip_fragment
                    )
                    parent = fragment_fn(token, parent, task, versions[path_id])

                self.session.commit()
                self._create_extra_tasks(task_tags, task, parent)

                # Extract ftrack path from structure and accessors.
                ftrack_shot_path = os.path.normpath(
                    self.ftrack_location.structure.get_resource_identifier(parent)
                )

                ftrack_path = str(os.path.join(
                    self.ftrack_location.accessor.prefix, ftrack_shot_path
                ))

                data = {
                    'component': parent,
                    'path': ftrack_path,
                    'published': False
                }

                self._components[root_item][track_item.name()][task.component_name()] = data
                self.add_ftrack_tag(track_item, task)

        self._create_project_progress_widget = None
        return filtered_export_items

    def add_ftrack_tag(self, original_item, task):
        ''' Add ftrack tag to *original_item* for *task*. '''

        if not hasattr(original_item, 'tags'):
            return

        # TrackItem
        item = task._item
        self.logger.info('Adding tag to {}'.format(original_item))
        try:
            root_item = original_item.parentTrack().name()
        except:
            root_item = original_item.name()

        localtime = time.localtime(time.time())

        start = item.sourceIn()
        end = item.sourceOut()

        start_handle, end_handle = task.outputHandles()

        task_id = str(task._preset.properties()['ftrack']['task_id'])
        task_name = task.component_name()
        data = self._components[root_item][original_item.name()][task_name]
        component = data['component']

        path = data['path']
        frame_offset = start if start else 0

        collate = getattr(task, '_collate', False)
        applying_retime = (task._retime and task._cutHandles is not None) or collate
        applied_retimes_str = '1' if applying_retime else '0'

        existing_tag = None
        for tag in original_item.tags():
            if (
                    tag.metadata().hasKey('tag.presetid') and
                    tag.metadata()['tag.presetid'] == task_id and
                    tag.metadata().hasKey('tag.task_name') and
                    tag.metadata()['tag.task_name'] == task_name
            ):
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
            '{0}'.format(task_name),
            ':/ftrack/image/default/ftrackLogoLight',
            False
        )
        tag.metadata().setValue('tag.provider', 'ftrack')
        tag.metadata().setValue('tag.task_name', task_name)

        tag.metadata().setValue('tag.presetid', task_id)
        tag.metadata().setValue('tag.component_id', component['id'])
        tag.metadata().setValue('tag.version_id', component['version']['id'])
        tag.metadata().setValue('tag.asset_id', component['version']['asset']['id'])
        tag.metadata().setValue('tag.version', str(component['version']['version']))
        tag.metadata().setValue('tag.path', path)
        tag.metadata().setValue('tag.description', 'ftrack {0}'.format(task_name))

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

        try:
            root_item = task._item.parentTrack().name()
        except:
            root_item = task._item.name()

        has_data = self._components.get(
            root_item, {}
        ).get(
            task._item.name(), {}
        ).get(task.component_name())

        if not has_data:
            return

        render_data = has_data

        output_path = render_data['path']

        task._exportPath = output_path
        task.setDestinationDescription(output_path)

        # Ensure output path exists.
        base_path = os.path.dirname(output_path)
        if not os.path.exists(base_path):
            self.logger.debug('ensuring folder: {}'.format(base_path))
            os.makedirs(base_path)

        def _makeNullPath():
            pass

        task._makePath = _makeNullPath

    def publish_result_component_event(self, render_task):
        ''' Event spawned when *render_task* frame is rendered. '''

        if not render_task._item:
            return

        try:
            root_item = render_task._item.parentTrack().name()
        except:
            root_item = render_task._item.name()

        has_data = self._components.get(
            root_item, {}
        ).get(
            render_task._item.name(), {}
        ).get(render_task.component_name())

        if not has_data:
            return

        render_data = has_data

        component = render_data['component']
        publish_path = render_data['path']
        is_published = render_data['published']

        if render_task.error():
            self.logger.warning('An Error occurred while rendering: {0}: {1}'.format(
                publish_path, render_task.error())
            )
            return

        if is_published:
            return

        start, end = self._get_start_end_frame(render_task)
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

        # remove accessor prefix from final component
        resource_identifier = publish_path.split(
            self.ftrack_location.accessor.prefix
        )[-1][1:]

        is_container = 'members' in component.keys()

        if is_container:
            member_path = '{} [{}-{}]'.format(resource_identifier, start, end)
            self.logger.info('Registering collection {}'.format(member_path))

            members = clique.parse(member_path)

            self.ftrack_location._register_components_in_location(
                component['members'], members
            )

        self.ftrack_location._register_component_in_location(
            component, resource_identifier
        )

        self.logger.debug('Publishing : {0}'.format(publish_path))

        publish_thumbnail = self._preset.properties()['ftrack'].get(
            'opt_publish_thumbnail'
        )

        publish_reviewable = self._preset.properties()['ftrack'].get(
            'opt_publish_reviewable'
        )

        self.logger.info('Publish Thumbnail: {}'.format(publish_thumbnail))
        self.logger.info('Publish Reviewable: {}'.format(publish_reviewable))

        # Add option to publish or not the thumbnail.
        if publish_thumbnail:
            self.publish_thumbnail(component, render_task)

        # Add option to publish or not the reviewable.
        if publish_reviewable:
            _, ext = os.path.splitext(publish_path)
            if ext == '.mov':
                component['version'].encode_media(publish_path)

        self.session.commit()
        render_data['published'] = True

    def publish_thumbnail(self, component, render_task):
        ''' Generate thumbnail *component* for *render_task*. '''
        source = render_task._item

        start = source.sourceIn()
        end = source.sourceOut()

        mid_frame = int(((end - start) / 2 ) + start)

        self.logger.info(
            'setting poster frame to {} for {}'.format(mid_frame, source)
        )

        thumbnail_qimage = source.thumbnail(mid_frame)
        thumbnail_file = tempfile.NamedTemporaryFile(
            prefix='hiero_ftrack_thumbnail', suffix='.png', delete=False
        ).name

        thumbnail_qimage_resized = thumbnail_qimage.scaledToWidth(
            1280, QtCore.Qt.SmoothTransformation
        )

        thumbnail_qimage_resized.save(thumbnail_file)
        version = component['version']
        version.create_thumbnail(thumbnail_file)
        version['task'].create_thumbnail(thumbnail_file)
        version['task']['parent'].create_thumbnail(thumbnail_file)

    def validate_ftrack_processing(self, export_items, preview):
        ''' Return whether the *export_items* and processor are valid to be rendered.

        In *preview* will not go through the whole validation, and return False by default.

        '''

        task_type = self._preset.properties()['ftrack']['task_type']
        asset_type_name = self._preset.properties()['ftrack']['asset_type_name']
        asset_name = self._preset.properties()['ftrack']['asset_name']

        for (export_path, preset) in self._exportTemplate.flatten():
            # Propagate properties from processor to tasks.
            preset.properties()['ftrack']['task_type'] = task_type
            preset.properties()['ftrack']['asset_type_name'] = asset_type_name
            preset.properties()['ftrack']['asset_name'] = asset_name

        if preview:
            return False
        else:
            self._validate_project_progress_widget = foundry.ui.ProgressTask('Validating settings.')
            errors = {}
            missing_assets_type = []
            duplicated_components = []

            non_matching_template_items = []

            num_items = len(self._exportTemplate.flatten()) + len(export_items)
            progress_index = 0

            for exportItem in export_items:

                item = exportItem.item()

                # Skip effects track items.
                if isinstance(item, (hiero.core.EffectTrackItem, hiero.core.Transition)):
                    self.logger.debug('Skipping {0}'.format(item))
                    continue

                project = item.project()
                parsing_template = template_manager.get_project_template(project)

                task_tags = set()
                task_types = self.schema(project).get_types('Task')

                try:
                    template_manager.match(item, parsing_template)
                except ftrack_connect_nuke_studio.exception.TemplateError:
                    self.logger.warning(
                        'Skipping {} as does not match {}'.format(
                            item, parsing_template['expression']
                        )
                    )
                    if item not in non_matching_template_items:
                        non_matching_template_items.append(item.name())
                    continue

                if not hasattr(item, 'tags'):
                    continue

                for tag in item.tags():
                    meta = tag.metadata()
                    if meta.hasKey('type') and meta.value('type') == 'ftrack':
                        task_name = meta.value('ftrack.name')
                        filtered_task_types = [
                            task_type for task_type in task_types if (
                                task_type['name'] == task_name
                            )
                        ]
                        if len(filtered_task_types) == 1:
                            task_tags.add(task_name)

                components = []

                for (export_path, preset) in self._exportTemplate.flatten():
                    # Build TaskData seed
                    taskData = hiero.core.TaskData(
                        preset,
                        item,
                        preset.properties()['exportRoot'],
                        export_path,
                        'v0',
                        self._exportTemplate,
                        project=item.project(),
                        resolver=self._preset.createResolver()
                    )
                    task = hiero.core.taskRegistry.createTaskFromPreset(
                        preset,
                        taskData
                    )

                    self.logger.info(
                        'Getting preset {} for deduplication'.format(
                            task.component_name()
                        )
                    )

                    if task.component_name() not in components:
                        components.append(task.component_name())
                    else:
                        duplicated_components.append((task.component_name(), task))

                    progress_index += 1

                    self._validate_project_progress_widget.setProgress(
                        int(100.0 * (float(progress_index) / float(num_items)))
                    )
                    asset_type_name = preset.properties()['ftrack']['asset_type_name']

                    ftrack_asset_type = self.session.query(
                        'AssetType where name is "{0}"'.format(asset_type_name)
                    ).first()

                    if not ftrack_asset_type and asset_type_name not in missing_assets_type:
                        missing_assets_type.append(asset_type_name)

                    try:
                        result = self.task_type(project)
                    except FtrackProcessorValidationError as error:
                        preset_errors = errors.setdefault(self, {})
                        preset_errors.setdefault('task_type', list(task_tags))

            self._validate_project_progress_widget = None

            # Raise validation window.
            if errors or missing_assets_type or duplicated_components:
                settings_validator = FtrackSettingsValidator(
                    self.session, errors,
                    missing_assets_type, duplicated_components
                )

                if settings_validator.exec_() != QtWidgets.QDialog.Accepted:
                    return False

                self.validate_ftrack_processing(export_items, preview)

            # Raise notification for error parsing items.
            if non_matching_template_items:
                item_warning = QtWidgets.QMessageBox().warning(
                    None,
                    'Error parsing Track Items',
                    'Some items failed to parse and will not be published\n'
                    '{} do you want to continue with the others ?'.format(
                        ', '.join(non_matching_template_items)
                    ),
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

        project_id = os.getenv('FTRACK_CONTEXTID')
        project = self.session.get('Project', project_id)

        self.logger.info('Project: {}'.format(project))
        key, value, label = 'project_name', str(project['full_name']), 'Create under project'
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
        self.project_options_widget.setDisabled(True)

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

        task_tags = sorted(list(task_tags)) or [self._preset.properties()['ftrack']['task_type']]
        key, value, label = 'task_type', list(task_tags), 'Publish to task'
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
        self.task_type_options_widget.update(True)

    def add_asset_name_options(self, parent_layout):
        '''Create asset name options widget with parent *parent_layout*.'''
        asset_name = self._preset.properties()['ftrack']['asset_name']
        key, value, label = 'asset_name', asset_name, 'Asset name'
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
        self.asset_name_options_widget.update(True)

    def add_thumbnail_options(self, parent_layout):
        '''Create thumbnail options widget with parent *parent_layout*.'''
        # Thumbanil generation.
        key, value, label = 'opt_publish_thumbnail', True, 'Publish thumbnail'
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
        key, value, label = 'opt_publish_reviewable', True, 'Publish reviewable'
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

        asset_type_names = [asset_type['name'] for asset_type in asset_types]
        key, value, label = 'asset_type_name', asset_type_names, 'Asset type'
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
        self.asset_type_options_widget.update(True)

    def add_task_templates_options(self, parent_layout):
        ''' Create task template options widget with parent *parent_layout*.'''
        self.template_widget_options_widget = Template(self._project)
        parent_layout.addRow('Shot template' + ':', self.template_widget_options_widget)

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
        self.set_ui_tweaks()
        return form_layout

    def addFtrackTaskUI(self, parent_layout, exportTemplate):
        current_task_name = self._preset.name()
        key, value, label = 'component_name', current_task_name, 'Component name'
        tooltip = 'Component Name'

        task_name_options_widget = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip

        )
        parent_layout.addRow(label + ':', task_name_options_widget)
