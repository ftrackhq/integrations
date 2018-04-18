
import tempfile
from QtExt import QtCore, QtWidgets

from . import FtrackBasePreset, FtrackBase

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import *


class FtrackProcessorPreset(FtrackBasePreset):
    def __init__(self, name, properties):
        super(FtrackProcessorPreset, self).__init__(name, properties)

    def set_ftrack_properties(self, properties):
        super(FtrackProcessorPreset, self).set_ftrack_properties(properties)


class FtrackProcessor(FtrackBase):
    def __init__(self, initDict):
        super(FtrackProcessor, self).__init__(initDict)

        # store a reference of the origial initialization data
        self._init_dict = initDict

        # store a reference of the ftrack properties for easier access
        self.ftrack_properties = self._preset.properties()['ftrack']

        # note we do resolve {ftrack_version} as part of the {ftrack_asset} function
        self.fn_mapping = {
            '{ftrack_project}': self._create_project_fragment,
            '{ftrack_sequence}': self._create_sequence_fragment,
            '{ftrack_shot}': self._create_shot_fragment,
            '{ftrack_task}': self._create_task_fragment,
            '{ftrack_asset}': self._create_asset_fragment,
            '{ftrack_component}': self._create_component_fragment
        }

        self._component = None

    def updateItem(self, originalItem, localtime):
        self.create_project_structure()
        self.addFtrackTag(originalItem, localtime)

    def addFtrackTag(self, originalItem, localtime):
        processor_id = str(self.ftrack_properties['processor_id'])

        existingTag = None
        for tag in originalItem.tags():
            if tag.metadata().hasKey('tag.presetid') and tag.metadata()['tag.presetid'] == processor_id:
                existingTag = tag
                break

        if existingTag:
            existingTag.metadata().setValue('tag.version_id', self._component['version']['id'])
            existingTag.metadata().setValue('tag.asset_id', self._component['version']['asset']['id'])
            existingTag.metadata().setValue('tag.version', str(self._component['version']['version']))
            self.logger.info('Updating tag: {0}'.format(existingTag))
            # Move the tag to the end of the list.
            originalItem.removeTag(existingTag)
            originalItem.addTag(existingTag)
            return

        timestamp = self.timeStampString(localtime)

        tag_name = '{0} {1}'.format(
            self.__class__.__name__,
            timestamp
        )

        tag = hiero.core.Tag(
            tag_name,
            ':/ftrack/image/default/ftrackLogoColor',
            False
        )

        tag.metadata().setValue('tag.presetid', processor_id)
        tag.metadata().setValue('tag.processor', self.__class__.__name__)
        tag.metadata().setValue('tag.component_id', self._component['id'])
        tag.metadata().setValue('tag.version_id', self._component['version']['id'])
        tag.metadata().setValue('tag.asset_id', self._component['version']['asset']['id'])
        tag.metadata().setValue('tag.version', str(self._component['version']['version']))

        tag.metadata().setValue('tag.description', 'Ftrack Entity')

        self.logger.info('Adding tag: {0} to item {1}'.format(tag, originalItem))
        originalItem.addTag(tag)

    def finishTask(self):
        component = self._component
        version = component['version']

        final_path = self._exportPath

        if '#' in self._exportPath:
            start, end = self.outputRange()

            # todo: Improve this logic
            final_path = '{0} [{1}-{2}]'.format(self._exportPath, start, end)

        self.session.create(
            'ComponentLocation', {
                'location_id': self.ftrack_location['id'],
                'component_id': component['id'],
                'resource_identifier': final_path
            }
        )
        # add option to publish or not the thumbnail
        if self.ftrack_properties['opt_publish_thumbnail']:
            self.publishThumbnail(component)

        self.session.commit()
        self.session.delete(component)
        #
        # if self.ftrack_properties['opt_publish_reviewable']:
        #     self.publishReviewable(component)

    def timeStampString(self, localtime):
        '''timeStampString(localtime)
        Convert a tuple or struct_time representing a time as returned by gmtime() or localtime() to a string formated YEAR/MONTH/DAY TIME.
        '''
        return time.strftime('%Y/%m/%d %X', localtime)

    def _makePath(self):
        # do not create any folder!
        self.logger.debug('Skip creating folder for : %s' % self.__class__.__name__)
        pass

    def publishThumbnail(self, component):
        source = self._item.source()
        thumbnail_qimage = source.thumbnail(source.posterFrame())
        thumbnail_file = tempfile.NamedTemporaryFile(prefix='hiero_ftrack_thumbnail', suffix='.png', delete=False).name
        thumbnail_qimage_resized = thumbnail_qimage.scaledToWidth(600, QtCore.Qt.SmoothTransformation)
        thumbnail_qimage_resized.save(thumbnail_file)
        version = component['version']
        version.create_thumbnail(thumbnail_file)
        version['task'].create_thumbnail(thumbnail_file)

    def publishReviewable(self, component):
        job = self.session.encode_media(component)
        print job

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
        task_type = [t for t in task_types if t['name'] == task_type_name][0]
        # self.logger.info('task_type: %s' % task_type)
        return task_type

    @property
    def task_status(self):
        task_status_name = self.ftrack_properties['task_status']
        task_statuses = self.schema.get_statuses('Task', self.task_type['id'])
        task_status = [t for t in task_statuses if t['name'] == task_status_name][0]
        # self.logger.info('task_status: %s' % task_status)
        return task_status

    @property
    def shot_status(self):
        shot_status_name = self.ftrack_properties['shot_status']
        shot_statuses = self.schema.get_statuses('Shot')
        shot_status = [t for t in shot_statuses if t['name'] == shot_status_name][0]
        # self.logger.info('shot_status: %s' % shot_status)
        return shot_status

    @property
    def asset_version_status(self):
        asset_status_name = self.ftrack_properties['asset_version_status']
        asset_statuses = self.schema.get_statuses('AssetVersion')
        asset_status = [t for t in asset_statuses if t['name'] == asset_status_name][0]
        # self.logger.info('asset_version_status: %s' % asset_status)
        return asset_status

    def asset_type_per_task(self, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        result = self.session.query(
            'AssetType where short is "{0}"'.format(asset_type)
        ).one()

        return result

    def _create_project_fragment(self, name, parent, task):
        project = self.session.query(
            'Project where name is "{0}"'.format(name)
        ).first()
        if not project:
            project = self.session.create('Project', {
                'name': name,
                'full_name': name + '_full',
                'project_schema': self.schema
            })
        return project

    def _create_sequence_fragment(self, name, parent, task):
        sequence = self.session.query(
            'Sequence where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()
        if not sequence:
            sequence = self.session.create('Sequence', {
                'name': name,
                'parent': parent
            })
        return sequence

    def _create_shot_fragment(self, name, parent, task):
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

    def _create_asset_fragment(self, name, parent, task):
        asset = self.session.query(
            'Asset where name is "{0}" and parent.id is "{1}"'.format(name, parent['parent']['id'])
        ).first()
        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent': parent['parent'],
                'type': self.asset_type_per_task(task)
            })

        comment = 'Published with: {0} From Nuke Studio : {1}.{2}.{3}'.format(
            self.__class__.__name__, *self.hiero_version_touple
        )

        version = self.session.create('AssetVersion', {
            'asset': asset,
            'status': self.asset_version_status,
            'comment': comment,
            'task': parent
        })

        return version

    def _create_task_fragment(self, name, parent, task):
        task = self.session.query(
            'Task where name is "{0}" and parent.id is "{1}"'.format(name, parent['id'])
        ).first()
        if not task:
            task = self.session.create('Task', {
                'name': name,
                'parent': parent,
                'status': self.task_status,
                'type': self.task_type
            })
        return task

    def _create_component_fragment(self, name, parent, task):
        component = parent.create_component('/', {
            'name': self.ftrack_properties['component_name']
        }, location=None)

        return component

    def _skip_fragment(self, name, parent, task):
        self.logger.warning('Skpping : {0}'.format(name))

    def create_project_structure(self):
        preset_name = self._preset.name()
        self.logger.info('Creating structure for : {0}'.format(preset_name))

        file_name = '{0}{1}'.format(
            self._preset.properties()['ftrack']['component_name'],
            self._preset.properties()['ftrack']['component_pattern']
        )
        resolved_file_name = self.resolvePath(file_name)

        path = self.resolvePath(self._shotPath)
        parent = None  # after the loop this will be containing the component object

        for template, token in zip(self._shotPath.split(os.path.sep), path.split(os.path.sep)):
            fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
            parent = fragment_fn(token, parent, self)

        self.session.commit()
        self._component = parent

        # extract ftrack path from structure and accessors
        ftrack_shot_path = self.ftrack_location.structure.get_resource_identifier(parent)

        # ftrack sanitize output path, but we need to retain the original on here
        # otherwise foo.####.ext becomes foo.____.ext
        tokens = ftrack_shot_path.split(os.path.sep)
        tokens[-1] = resolved_file_name
        ftrack_shot_path = os.path.sep.join(tokens)

        ftrack_path = str(os.path.join(self.ftrack_location.accessor.prefix, ftrack_shot_path))
        self._exportPath = ftrack_path
        self.setDestinationDescription(ftrack_path)


class FtrackProcessorUI(FtrackBase):
    def __init__(self, preset):
        super(FtrackProcessorUI, self).__init__(preset)
        self._nodeSelectionWidget = None

    def addFtrackUI(self, widget, exportTemplate):
        formLayout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(formLayout)
        formLayout.addDivider("Ftrack Options")

        # ----------------------------------
        # Thumbanil generation

        key, value, label = 'opt_publish_thumbnail', True, 'Publish Thumbnail'
        thumbnail_tooltip = 'Generate and upload thumbnail'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ":",
            tooltip=thumbnail_tooltip
        )
        formLayout.addRow(label + ":", uiProperty)

        # ----------------------------------
        # Component Name

        key, value, label = 'component_name', '', 'Component Name'
        component_tooltip = 'Set Component Name'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ":",
            tooltip=component_tooltip
        )
        formLayout.addRow(label + ":", uiProperty)
