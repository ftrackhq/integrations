import os
import hiero
import logging
import ftrack_api
import time

FTRACK_SHOW_PATH = os.path.join(
    '{ftrack_project}',
    '{ftrack_task}',
    '{ftrack_asset}',
    '{ftrack_component}'
)

FTRACK_SEQUENCE_PATH = os.path.join(
    '{ftrack_project}',
    '{ftrack_shot}',
    '{ftrack_task}',
    '{ftrack_asset}',
    '{ftrack_component}'
)

FTRACK_SHOT_PATH = os.path.join(
    '{ftrack_project}',
    '{ftrack_sequence}',
    '{ftrack_shot}',
    '{ftrack_task}',
    '{ftrack_asset}',
    '{ftrack_component}'
)


class FtrackProcessorError(Exception):
    pass

class FtrackProcessorValidationError(FtrackProcessorError):
    pass


class FtrackBase(object):
    '''
    wrap ftrack functionalities and methods
    '''

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)
        self.session = ftrack_api.Session()

    def timeStampString(self, localtime):
        return time.strftime('%Y/%m/%d %X', localtime)

    @property
    def hiero_version_touple(self):
        return (
            hiero.core.env['VersionMajor'],
            hiero.core.env['VersionMinor'],
            hiero.core.env['VersionRelease'].split('v')[-1]
        )

    @property
    def ftrack_location(self):
        result = self.session.pick_location()
        # self.logger.info('location: %s' % result)
        return result

    @property
    def ftrack_origin_location(self):
        return self.session.query(
            'Location where name is "ftrack.origin"'
        ).one()

    @property
    def ftrack_server_location(self):
        return self.session.query(
            'Location where name is "ftrack.server"'
        ).one()

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
        try:
            task_type = [t for t in task_types if t['name'] == task_type_name][0]
        except Exception as e:
            raise FtrackProcessorError(e)
        # self.logger.info('task_type: %s' % task_type)
        return task_type

    @property
    def task_status(self):
        task_status_name = self.ftrack_properties['task_status']
        task_statuses = self.schema.get_statuses('Task', self.task_type['id'])
        try:
            task_status = [t for t in task_statuses if t['name'] == task_status_name][0]
        except Exception as e:
            raise FtrackProcessorError(e)
        # self.logger.info('task_status: %s' % task_status)
        return task_status

    @property
    def shot_status(self):
        shot_status_name = self.ftrack_properties['shot_status']
        shot_statuses = self.schema.get_statuses('Shot')
        try:
            shot_status = [t for t in shot_statuses if t['name'] == shot_status_name][0]
        except Exception as e:
            raise FtrackProcessorError(e)
        # self.logger.info('shot_status: %s' % shot_status)
        return shot_status

    @property
    def asset_version_status(self):
        asset_status_name = self.ftrack_properties['asset_version_status']
        asset_statuses = self.schema.get_statuses('AssetVersion')
        try:
            asset_status = [t for t in asset_statuses if t['name'] == asset_status_name][0]
        except Exception as e:
            raise FtrackProcessorError(e)
        # self.logger.info('asset_version_status: %s' % asset_status)
        return asset_status

    def asset_type_per_task(self, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        try:
            result = self.session.query(
                'AssetType where short is "{0}"'.format(asset_type)
            ).one()
        except Exception as e:
            raise FtrackProcessorError(e)
        return result


class FtrackBasePreset(FtrackBase):
    def __init__(self, name, properties, **kwargs):
        super(FtrackBasePreset, self).__init__(name, properties)
        self.set_export_root()
        self.set_ftrack_properties(properties)

    def isFtrackValid(self):
        errors = []
        for setting in [self.schema, self.task_type ,self.task_status, self.shot_status, self.asset_version_status]:
            try:
                setting()
            except Exception as e:
                errors.append(e)
        if errors:
            return (False,errors)

        return (True, '')

    def set_ftrack_properties(self, properties):
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default task properties
        self.properties()['ftrack']['component_name'] = None
        self.properties()['ftrack']['component_pattern'] = None
        self.properties()['ftrack']['task_type'] = 'Generic'

        # add placeholders for default processor
        self.properties()['ftrack']['project_schema'] = 'Film Pipeline'
        self.properties()['ftrack']['task_status'] = 'Not Started'
        self.properties()['ftrack']['shot_status'] = 'In progress'
        self.properties()['ftrack']['asset_version_status'] = 'WIP'
        self.properties()['ftrack']['processor_id'] = hash(self.__class__.__name__)

        # options
        self.properties()['ftrack']['opt_publish_thumbnail'] = True

    def set_export_root(self):
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project(self, task):
        return task.projectName()

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[0]

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        if not isinstance(trackItem, hiero.core.Sequence):
            return trackItem.name().split('_')[1]
        else:
            return trackItem.name()

    def resolve_ftrack_task(self, task):
        return self.properties()['ftrack']['task_type']

    def resolve_ftrack_asset(self, task):
        return task._preset.name()

    def resolve_ftrack_component(self, task):
        component_name = self.properties()['ftrack']['component_name']
        extension = self.properties()['ftrack']['component_pattern']
        component_full_name = '{0}{1}'.format(component_name, extension)
        return component_full_name

    def addFtrackResolveEntries(self, resolver):

        resolver.addResolver(
            '{ftrack_project}',
            'Ftrack project name.',
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            '{ftrack_sequence}',
            'Ftrack sequence name.',
            lambda keyword, task: self.resolve_ftrack_sequence(task)
        )

        resolver.addResolver(
            '{ftrack_shot}',
            'Ftrack shot name.',
            lambda keyword, task: self.resolve_ftrack_shot(task)
        )

        resolver.addResolver(
            '{ftrack_task}',
            'Ftrack task name.',
            lambda keyword, task: self.resolve_ftrack_task(task)
        )

        resolver.addResolver(
            '{ftrack_asset}',
            'Ftrack asset name.',
            lambda keyword, task: self.resolve_ftrack_asset(task)
        )

        resolver.addResolver(
            '{ftrack_component}',
            'Ftrack component name.',
            lambda keyword, task: self.resolve_ftrack_component(task)
        )

