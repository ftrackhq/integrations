# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline.utils import asynchronous


class FtrackPublishPlugin(plugin.FinaliserPlugin):
    plugin_name = 'result'

    def __init__(self, session):
        super(FtrackPublishPlugin, self).__init__(session)
        self.component_functions = {
            'thumbnail':  self.create_thumbnail,
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

    @asynchronous
    def create_thumbnail(self, asset_version, component_name, component_path):
        asset_version.create_thumbnail(component_path)

    @asynchronous
    def create_reviewable(self, asset_version, component_name, component_path):
        asset_version.encode_media(component_path)

    def run(self, context=None, data=None, options=None):
        output = self.output

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

        self.session.commit()

        results = {}

        for component_name, component_path in data.items():
            publish_component_fn = self.component_functions.get(
                component_name, self.create_component
            )
            publish_component_fn(asset_version, component_name, component_path)
            results[component_name] = True

        output.update(results)

        self.session.commit()

        self.logger.debug("publishing: {} to {} as {}".format(data, context,
                                                              asset_object))

        return output


def register(api_object, **kw):
    plugin = FtrackPublishPlugin(api_object)
    plugin.register()
