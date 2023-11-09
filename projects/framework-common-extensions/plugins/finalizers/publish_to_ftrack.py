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
            required_output_value=None,
        )

    # TODO: review this code to check if the rollback works as it is.
    def run(self, context_data=None, data=None, options=None):
        '''
        This method expects to receive a dictionary in the given *data* with all
        the previous steps plugin results. Will look for all the components
        exporter plugins in the given *data* and will publish the result to its
        component name in ftrack.
        '''

        # Get components to publish
        components = data.get('component')
        component_names = list(components.keys())
        publish_components = {}
        for component_name in component_names:
            if not components[component_name].get('exporter'):
                continue
            # Get the exporter result
            exporter_results = []
            for plugin, values in components[component_name][
                'exporter'
            ].items():
                if type(values) != list:
                    values = [values]
                exporter_results.extend(values)

            publish_components[component_name] = exporter_results

        # TODO: implement version_dependencies
        version_dependencies = []
        comment = context_data[0]['comment']
        status_id = context_data[0]['status_id']
        # TODO: Discuss with the team, how we pass the asset type, in the
        #  tool_config or in the context plugin? Right now only capable of publishing script asset type
        # Get Context object
        context_object = self.session.query(
            'select name, parent, parent.name from Context where '
            'id is "{}"'.format(self.context_data[0]['context_id'])
        ).one()

        # Get Status object
        status_object = self.session.query(
            'Status where id is "{}"'.format(status_id)
        ).one()

        if 'asset_id' in context_data[0]:
            # An explicit asset is provided
            asset_entity_object = self.session.query(
                'Asset where id is "{}"'.format(context_data[0]['asset_id'])
            ).first()
        else:
            # Query/identify asset
            # TODO, remove the script later one once this changes are implemented
            #  in the generic context plugin
            asset_type_name = (
                self.context_data[0].get('asset_type_name') or 'script'
            )
            asset_name = context_data[0].get('asset_name') or asset_type_name

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

            # Set dependencies
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
                "Error occurred during the run method, trying "
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
                asset_entity_object, self.context_data[0], asset_entity_object
            )
        )

        return_dict = {
            "asset_version_id": asset_version_object['id'],
            "asset_id": asset_entity_object["id"],
            "component_names": list(results.keys()),
        }

        return return_dict

    def _create_new_asset(
        self, asset_name, asset_type_object, asset_parent_object
    ):
        asset_entity = self.session.create(
            'Asset',
            {
                'name': asset_name,
                'type': asset_type_object,
                'parent': asset_parent_object,
            },
        )
        self.logger.debug('Successfully created asset: {}'.format(asset_name))
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
