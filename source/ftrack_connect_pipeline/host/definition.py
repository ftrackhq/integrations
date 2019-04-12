# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import ftrack_api
import json

from qtpy import QtCore

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import schema
from ftrack_connect_pipeline.event import EventManager

logger = logging.getLogger(__name__)


class BaseDefinitionManager(object):

    def result(self, *args, **kwargs):
        '''Return the result definitions.'''
        return self.__registry

    def __init__(self, session, schema_type, validator):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(BaseDefinitionManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.__registry = {}
        self.session = session
        self.event_manager = EventManager(self.session)
        self._validator = validator
        self._schema_type = schema_type
        self.register(schema_type)

    def validate(self, data):
        '''validate definitions against schema, coming from *data*.'''
        try:
            self._validator(data)
        except Exception as error:
            self.logger.warn(error)
            return False

        return True

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']
        result = None
        try:
            result = json.loads(raw_result)
        except Exception as error:
            self.logger.warning(
                'Failed to read definition {}, error :{} for {}'.format(
                    raw_result, error, self._schema_type
                )
            )

        if not result or not self.validate(result):
            return

        name = result['name']
        if name in self.__registry:
            self.logger.warning('{} already registered!'.format(name))
            return

        self.logger.info('Registering {}'.format(result['name']))
        self.__registry[name] = result

    def register(self, schema_type):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': str(schema_type)
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_definition,
            remote=True
        )

    def _discover_plugin(self, plugin, plugin_type):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
        plugin_name = plugin['plugin']

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_PLUGIN_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'plugin',
                    'host': self.host
                }
            }
        )

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )


        if plugin_result:
            plugin_result = plugin_result[0]

        return plugin_result


class PackageDefinitionManager(BaseDefinitionManager):
    '''Package schema manager class.'''

    def __init__(self, session):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(PackageDefinitionManager, self).__init__(session, 'package', schema.validate_package)


class LoaderDefinitionManager(BaseDefinitionManager):

    @property
    def packages(self):
        '''return available packages definitions.'''
        return self.package_manager.result()

    def __init__(self, package_manager, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(LoaderDefinitionManager, self).__init__(package_manager.session, 'loader', schema.validate_loader)
        self.package_manager = package_manager
        self.host = host

    def validate(self, data):
        schema_validation = super(LoaderDefinitionManager, self).validate(data)
        # TODO validate consistency of components against package definition also discover plugins
        return schema_validation


class PublisherDefinitionManager(BaseDefinitionManager):

    @property
    def packages(self):
        '''return available packages definitions.'''
        return self.package_manager.result()

    def __init__(self, package_manager, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(PublisherDefinitionManager, self).__init__(package_manager.session, 'publisher', schema.validate_publisher)
        self.package_manager = package_manager
        self.host = host

    def validate_plugins(self, data):
        # discover context plugins
        package_name = data['package']
        context_plugins = data[constants.CONTEXT]
        for context_plugin in context_plugins:
            if not self._discover_plugin(context_plugin, constants.CONTEXT):
                self.logger.warning(
                    'Could not discover plugin {} for {} in {}'.format(
                        context_plugin['plugin'], constants.CONTEXT, package_name
                    )
                )
                return False

        # discover component plugins
        component_plugins = data[constants.COMPONENTS]
        for component_name, component_stages in component_plugins.items():
            for component_stage, plugins in component_stages.items():
                for plugin in plugins:
                    if not self._discover_plugin(plugin, component_stage):
                        self.logger.warning(
                            'Could not discover plugin {} for stage {} in {}'.format(
                                plugin['plugin'], component_stage, package_name
                            )
                        )
                        return False

        # get publish plugins
        publisher_plugins = data[constants.PUBLISH]
        for publisher_plugin in publisher_plugins:
            if not self._discover_plugin(publisher_plugin, constants.PUBLISH):
                self.logger.warning(
                    'Could not discover plugin {} for {} in {}'.format(
                        publisher_plugin['plugin'], constants.PUBLISH, package_name
                    )
                )
                return False

        return True

    def validate_components(self, data):
        '''
        validate if the publisher defines the correct components based on the
        package definition.
        '''

        package_components = dict([
                (package['name'], package.get('optional', False)) for package
                in self.packages[data['package']]['components']
            ]
        )

        publisher_components = data['components'].keys()

        # check if the mandatory components defined in the package definition
        # are available in the publisher definition.
        for package_component_name, optional in package_components.items():
            if optional:
                continue

            if package_component_name not in publisher_components:
                self.logger.warning(
                    '{} is not defined in {}'.format(
                        package_component_name, data['package']
                    )
                )
                return False

        # check if the components defined in the publisher
        # are all available of the package definition
        for publisher_component in publisher_components:
            if publisher_component not in package_components.keys():
                self.logger.warning(
                    '{} is not found in {}'.format(
                        publisher_component, package_components.keys()
                    )
                )
                return False

        return True

    def validate_packages(self, data):
        '''validate if the publisher package type is defined in the packages'''
        package_validation = data['package'] in self.packages
        if not package_validation:
            self.logger.warning(
                'Publisher {} is not among the validated packages: {}'.format(
                    data['package'], self.packages.keys()
                )
            )
        return package_validation

    def validate(self, data):
        '''main validate function of *data*'''
        schema_validation = super(PublisherDefinitionManager, self).validate(data)

        if not schema_validation:
            return False

        package_validation = self.validate_packages(data)
        if not package_validation:
            return False

        components_validation = self.validate_components(data)
        if not components_validation:
            return False

        plugins_validation = self.validate_plugins(data)
        if not plugins_validation:
            return False

        return True


class DefintionManager(QtCore.QObject):
    '''class wrapper to contain all the definition managers.'''

    def __init__(self, session, host, hostid):
        self.session = session
        self.packages = PackageDefinitionManager(session)
        self.loaders = LoaderDefinitionManager(self.packages, host)
        self.publishers = PublisherDefinitionManager(self.packages, host)

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.type=publisher and data.pipeline.hostid={}'.format(
                constants.PIPELINE_REGISTER_DEFINITION_TOPIC, hostid),
            self.publishers.result
        )

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.type=loader and data.pipeline.hostid={}'.format(
                constants.PIPELINE_REGISTER_DEFINITION_TOPIC, hostid),
            self.loaders.result
        )

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.type=package and data.pipeline.hostid={}'.format(
                constants.PIPELINE_REGISTER_DEFINITION_TOPIC, hostid),
            self.packages.result
        )



