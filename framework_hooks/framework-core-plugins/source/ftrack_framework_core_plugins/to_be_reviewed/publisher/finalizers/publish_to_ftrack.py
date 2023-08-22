# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import traceback

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

# TODO: review and cleanup this code
class PublishToFtrack(BasePlugin):
    name = 'publish_to_ftrack'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_FINALIZER_TYPE
    '''Print given arguments'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None
        )

    # TODO: review this code to check if the rollback works as it is.
    def run(self, context_data=None, data=None, options=None):
        self.logger.debug("given context_data: {}".format(context_data))
        self.logger.debug("given data: {}".format(data))
        self.logger.debug("given options: {}".format(options))
        # TODO: Make it easier to get the exporter result.
        # Return the exporter result
        publish_components = {}
        for step in self.plugin_data:
            if step['type'] == constants.definition.COMPONENT:
                component_name = step['name']
                publish_components[component_name] =  []
                for stage in step['result']:
                    for plugin in stage['result']:
                        publish_components[component_name].append(
                            plugin['plugin_method_result']
                        )

        # TODO: implement version_dependencies
        version_dependencies = []
        comment = context_data['comment']
        status_id = context_data['status_id']
        asset_name = context_data['asset_name']
        # TODO: Discuss with the team, how we pass the asset type, in the
        #  definition or in the context plugin? Right now only capable of publishing script asset type
        asset_type_name = 'script'  # self.context_data['asset_type_name']

        # Get Status object
        status_object = self.session.query(
            'Status where id is "{}"'.format(status_id)
        ).one()

        # Get Context object
        context_object = self.session.query(
            'select name, parent, parent.name from Context where '
            'id is "{}"'.format(
                self.context_data['context_id']
            )
        ).one()

        # Get Asset type object
        asset_type_object = self.session.query(
            'AssetType where short is "{}"'.format(asset_type_name)
        ).first()

        # Get Asset parent object
        asset_parent_object = context_object['parent']

        # Get Asset entity object
        asset_entity_object = self.session.query(
            'Asset where name is "{}" and type.short is "{}" and '
            'parent.id is "{}"'.format(
                asset_name, asset_type_name, asset_parent_object['id']
            )
        ).first()

        # Create asset object if not exist
        if not asset_entity_object:
            asset_entity_object = self._create_new_asset(
                asset_name, asset_type_object, asset_parent_object
            )

        rollback = False
        try:
            # Generate asset version
            asset_version_object = self._create_new_asset_version(
                asset_entity_object, context_object, comment, status_object
            )

            # Set dependnecies
            if version_dependencies:
                for dependency in version_dependencies:
                    asset_version_object['uses_versions'].append(dependency)

            # Commit the session
            self.session.commit()

            self.logger.debug(
                'Successfully created assetversion: {}'.format(
                    asset_version_object['version']
                )
            )

            # Undo version creation from this point in case it fails
            rollback = True

            results = {}

            for component_name, paths in publish_components.items():
                # TODO: allow multiple paths
                if component_name == 'thumbnail':
                    self._create_thumbnail(
                        asset_version_object,
                        component_name,
                        paths[0],
                    )
                elif component_name == 'reviewable':
                    self._create_reviewable(
                        asset_version_object,
                        component_name,
                        paths[0],
                    )
                else:
                    self._create_component(
                        asset_version_object,
                        component_name,
                        paths[0],
                    )
                results[component_name] = True
            self.session.commit()
            rollback = False
        except:
            # An exception occurred when creating components,
            # return its traceback as error message
            tb = traceback.format_exc()
            self.status = constants.status.EXCEPTION_STATUS
            self.message = (
                "Error occurred during the post_execute_callback_hook, trying "
                "to create a new version and components of the finalizer_plugin: "
                "{} \n error: {}".format(self.name, str(tb))
            )
            return publish_components
        finally:
            if rollback:
                self.session.reset()
                self.logger.warning("Rolling back asset version creation")
                self.session.delete(asset_version_object)
                self.session.commit()

        self.logger.debug(
            "publishing: {} to {} as {}".format(
                self.plugin_data, self.context_data, asset_entity_object
            )
        )

        return_dict = {
            "asset_version_id": asset_version_object['id'],
            "asset_id": asset_entity_object["id"],
            "component_names": list(results.keys()),
        }

        return return_dict

    def _create_new_asset(self, asset_name, asset_type_object, asset_parent_object):
        asset_entity = self.session.create(
            'Asset',
            {
                'name': asset_name,
                'type': asset_type_object,
                'parent': asset_parent_object,
            },
        )
        self.logger.debug(
            'Successfully created asset: {}'.format(asset_name)
        )
        return asset_entity

    def _create_new_asset_version(
            self, asset_entity, context_object, comment, status_object
    ):
        asset_version_object = self.session.create(
            'AssetVersion',
            {
                'asset': asset_entity,
                'task': context_object,
                'comment': comment,
                'status': status_object,
            },
        )
        return asset_version_object

    def _create_component(
        self, asset_version_entity, component_name, component_path
    ):
        '''
        Creates a ftrack component on the given *asset_version_entity* with the given
        *component_name* pointing to the given *component_path*

        *asset_version_entity* : instance of
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

        asset_version_entity.create_component(
            component_path, data={'name': component_name}, location=location
        )

    def _create_thumbnail(
        self, asset_version_entity, component_name, component_path
    ):
        '''
        Creates and uploads an ftrack thumbnail for the given
        :class:`ftrack_api.entity.asset_version.AssetVersion` from the given
        *component_path*

        *component_path* : path to the thumbnail.
        '''
        asset_version_entity.create_thumbnail(component_path)
        os.remove(component_path)

    def _create_reviewable(
        self, asset_version_entity, component_name, component_path
    ):
        '''
        Encodes the ftrack media for the given
        :class:`ftrack_api.entity.asset_version.AssetVersion` from the given
        *component_path*

        *component_path* : path to the image or video.
        '''
        asset_version_entity.encode_media(component_path)
        os.remove(component_path)
