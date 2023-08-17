# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import traceback
import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants

#TODO: double check we are allowed to do this, or we should not use constants
#  here, or have host available in base plugin to be able to do something
#  like: host.constants.stage_types.COLLECTOR


#TODO: if we want to expose this to clients, this can be moved to
# framework_core_plugins same for the finalizer one.
# TODO: maybe this should not be a base Finalizer or anything like that, this
#  should simply be a post finalizer plugin and the execute method does the
#  publish to ftrack, so no hidden code anywhere.
#  (or another finalizer thhat is why we can put a list of plugins.)
class BaseFinalizerPlugin(BasePlugin):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # conviniance for the user when crreating its own plugin.
    name = None
    plugin_type = None
    host_type = None

    @property
    def version_dependencies(self):
        return self._version_dependencies

    @property
    def component_functions(self):
        return self._component_functions

    def __init__(self, event_manager, host_id, ftrack_object_manager):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(BaseFinalizerPlugin, self).__init__(
            event_manager, host_id, ftrack_object_manager
        )
        self._version_dependencies = []
        self._component_functions = {
            'thumbnail': self._create_thumbnail,
            'reviewable': self._create_reviewable,
        }

    #TODO: this should be an ABC
    def check_dependencies(self):
        self._version_dependencies = []

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
    # TODO: review this code to check if the rollback works as it is.
    def post_execute_callback_hook(self, result):
        comment = self.context_data['comment']
        status_id = self.context_data['status_id']
        asset_name = self.context_data['asset_name']
        # TODO: Discuss with the team, how we pass the asset type, in the
        #  definition or in the context plugin? Right now only capable of publishing script asset type
        asset_type_name = 'script'#self.context_data['asset_type_name']

        # Get Status object
        status_object = self.session.query(
            'Status where id is "{}"'.format(status_id)
        ).one()

        #Get Context object
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
            if self.version_dependencies:
                for dependency in self.version_dependencies:
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

            for component_name, paths in result.items():
                publish_component_fn = (
                    self.component_functions.get(
                        component_name, self._create_component
                    )
                )
               # TODO: allow multiple paths
                publish_component_fn(
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
            return result
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
        # TODO: check if we need to setup this as the result of the plugin... (I don't think we need this info)
        return return_dict



