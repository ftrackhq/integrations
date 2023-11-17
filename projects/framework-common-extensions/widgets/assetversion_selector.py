# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets

from ftrack_framework_widget.widget import FrameworkWidget
from ftrack_qt.widgets.selectors import AssetSelector


class AssetVersionSelectorWidget(FrameworkWidget, QtWidgets.QWidget):
    """Main class to represent an asset version selector widget."""

    name = "assetversion_selector"
    ui_type = "qt"

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        """initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        """

        QtWidgets.QWidget.__init__(self, parent=parent)
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_config,
            dialog_connect_methods_callback,
            dialog_property_getter_connection_callback,
            parent=parent,
        )

        self._assetversion_selector = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        self._assetversion_selector = AssetSelector(
            AssetSelector.MODE_SELECT_ASSETVERSION,
            self._on_fetch_assets_callback,
            self.session,
            fetch_assetversions=self._on_fetch_assetversions_callback(),
        )
        self.layout().addLayout(self._assetversion_selector)

    def post_build(self):
        """Perform post-construction operations."""
        self._assetversion_selector.versionChanged.connect(
            self._on_version_changed_callback
        )

    def _on_fetch_assets_callback(self):
        '''Return assets back to asset selector'''
        # TODO: To be moved to a plugin when ui_hook is implemented
        context_id = self.context_id

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                self.plugin_options.get('asset_type_name')
            )
        ).first()

        # Determine if we have a task or not
        context = self.session.get('Context', context_id)
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []
        if context.entity_type == 'Task':
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where versions.task.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        else:
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where parent.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        return list(assets)

    def _on_fetch_assetversions_callback(self, asset_entity):
        '''Query ftrack for all version beneath *asset_entity*'''
        # TODO: To be moved to a plugin when ui_hook is implemented
        result = []
        for version in self.session.query(
            'select version, id '
            'from AssetVersion where task.id is {} and asset_id is {} order by'
            ' version descending'.format(self.context_id, asset_entity['id'])
        ).all():
            result.append((version, True))
        return result

    def _on_version_changed_callback(self, assetversion_entity):
        if assetversion_entity:
            print(
                '@@@ {} {}({})'.format(
                    assetversion_entity['asset']['name'],
                    assetversion_entity['version'],
                    assetversion_entity['id'],
                )
            )
        else:
            print('@@@ None')

    def run_plugin_callback(self, plugin_info):
        # Check the result of the desired method
        if plugin_info["plugin_widget_id"] != self.id:
            return

        if (
            plugin_info["plugin_method"] == "fetch"
            and plugin_info["plugin_method_result"]
        ):
            # TODO: Make sure that all fetch widgets have set_data_items method in it.
            self.current_fetch_widget.set_data_items(
                plugin_info["plugin_method_result"]
            )

    def on_context_updated(self):
        '''Re-fetch from plugin due to context change.'''
        self.fetch()
