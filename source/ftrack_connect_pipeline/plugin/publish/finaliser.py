# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base


class PublisherFinaliserPlugin(base.BaseFinaliserPlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
    return_type = dict
    plugin_type = constants.PLUGIN_PUBLISHER_FINALISER_TYPE
    _required_output = {}
    version_dependencies = []

    def __init__(self, session):
        '''Initialise FinaliserPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(PublisherFinaliserPlugin, self).__init__(session)
        self.component_functions = {
            'thumbnail': self.create_thumbnail,
            'reviewable': self.create_reviewable
        }

    def create_component(self, asset_version, component_name, component_path):
        self.logger.info(
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
        asset_version.create_thumbnail(component_path)
        os.remove(component_path)

    def create_reviewable(self, asset_version, component_name, component_path):
        asset_version.encode_media(component_path)
        os.remove(component_path)

    def _run(self, event):
        super_result = super(PublisherFinaliserPlugin, self)._run(event)

        context = event['data']['settings']['context']
        data = event['data']['settings']['data']

        comment = context['comment']
        status_id = context['status_id']
        asset_name = context['asset_name']
        asset_type = context['asset_type']

        status = self.session.get('Status', status_id)

        context_object = self.session.get('Context', context['context_id'])
        asset_type_object = self.session.query(
            'AssetType where short is "{}"'.format(asset_type)).first()
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

        for component_name, component_path in data.items():
            publish_component_fn = self.component_functions.get(
                component_name, self.create_component
            )
            publish_component_fn(asset_version, component_name, component_path)
            results[component_name] = True

        self.session.commit()

        self.logger.debug("publishing: {} to {} as {}".format(data, context,
                                                              asset_object))

        return super_result