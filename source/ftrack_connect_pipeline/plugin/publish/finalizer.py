# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class PublisherFinalizerPlugin(base.BaseFinalizerPlugin):
    '''
    Base Publisher Finalizer Plugin Class inherits from
    :class:`~ftrack_connect_pipeline.plugin.base.BaseFinalizerPlugin`
    '''
    return_type = dict
    '''Required return type'''
    plugin_type = constants.PLUGIN_PUBLISHER_FINALIZER_TYPE
    '''Type of the plugin'''
    _required_output = {}
    '''Required return output'''
    version_dependencies = []
    '''Ftrack dependencies of the current asset version'''

    def __init__(self, session):
        super(PublisherFinalizerPlugin, self).__init__(session)
        self.component_functions = {
            'thumbnail': self.create_thumbnail,
            'reviewable': self.create_reviewable
        }

    def create_component(self, asset_version, component_name, component_path):
        '''
        Creates an ftrack component on the given *asset_version* with the given
        *component_name* pointing to the given *component_path*

        *asset_version* : instance of
        :class:`ftrack_api.entity.asset_version.AssetVersion`

        *component_name* : Name of the component to be created.

        *component_path* : Linked path of the component data.
        '''
        self.logger.debug(
            'publishing component:{} to from {}'.format(
                component_name, component_path
            )
        )
        location = self.session.pick_location()

        asset_version.create_component(
            component_path,
            data={'name': component_name},
            location=location
        )

    def create_thumbnail(self, asset_version, component_name, component_path):
        '''
        Creates and uploads an ftrack thumbnail for the given
        :class:`ftrack_api.entity.asset_version.AssetVersion` from the given
        *component_path*

        *component_path* : path to the thumbnail.
        '''
        asset_version.create_thumbnail(component_path)
        os.remove(component_path)

    def create_reviewable(self, asset_version, component_name, component_path):
        '''
        Encodes the ftrack media for the given
        :class:`ftrack_api.entity.asset_version.AssetVersion` from the given
        *component_path*

        *component_path* : path to the image or video.
        '''
        asset_version.encode_media(component_path)
        os.remove(component_path)

    def _run(self, event):
        '''
        Overrides the Callback function of the event
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC`
        :meth:`ftrack_connect_pipeline.plugin._run`.
        Which runs the method passed in the given
        *event* ['data']['pipeline']['method'].

        Once the base method is called, this function creates a new
        :class:`ftrack_api.entity.asset_version.AssetVersion` with all the
        required information as component, reviewable, thumbnail, etc... And
        commits the ftrack session.

        Returns a diccionary with the result information of the called method.

        *event* : Diccionary returned when the event topic
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC` is
        called.

        '''
        super_result = super(PublisherFinalizerPlugin, self)._run(event)

        if super_result.get('status') != constants.SUCCESS_STATUS:
            return super_result

        context = event['data']['settings']['context']
        data = event['data']['settings']['data']

        comment = context['comment']
        status_id = context['status_id']
        asset_name = context['asset_name']
        asset_type = context['asset_type']

        status = self.session.query('Status where id is "{}"'.format(status_id)).one()
        context_object = self.session.query(
            'select name, parent, parent.name from Context where id is "{}"'.format(
                context['context_id']
            )
        ).one()

        asset_type_object = self.session.query(
            'AssetType where short is "{}"'.format(asset_type)
        ).first()

        asset_parent_object = context_object['parent']

        asset_object = self.session.query(
            'Asset where name is "{}" and type.short is "{}" and '
            'parent.id is "{}"'.format(
                asset_name, asset_type, asset_parent_object['id'])).first()

        if not asset_object:
            asset_object = self.session.create('Asset', {
                'name': asset_name,
                'type': asset_type_object,
                'parent': asset_parent_object
            })

        asset_version = self.session.create('AssetVersion', {
            'asset': asset_object,
            'task': context_object,
            'comment': comment,
            'status': status
        })

        if self.version_dependencies:
            for dependency in self.version_dependencies:
                asset_version['uses_versions'].append(dependency)

        self.session.commit()

        results = {}

        for step in data:
            if step['type'] == constants.COMPONENT:
                component_name = step['name']
                for stage in step['result']:
                    for plugin in stage['result']:
                        for component_path in plugin['result']:
                            publish_component_fn = self.component_functions.get(
                                component_name, self.create_component
                            )
                            publish_component_fn(
                                asset_version,
                                component_name,
                                component_path
                            )
                            results[component_name] = True
        self.session.commit()

        self.logger.debug("publishing: {} to {} as {}".format(data, context,
                                                              asset_object))

        return super_result