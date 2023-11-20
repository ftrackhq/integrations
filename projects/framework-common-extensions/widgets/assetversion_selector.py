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
        group_config,
        on_set_plugin_option,
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
            group_config,
            on_set_plugin_option,
            parent,
        )

        self._label = None
        self._assetversion_selector = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build(self):
        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)

        self._assetversion_selector = AssetSelector(
            AssetSelector.MODE_SELECT_ASSETVERSION,
            self._on_fetch_assets_callback,
            self.session,
            fetch_assetversions=self._on_fetch_assetversions_callback,
        )

        self.layout().addWidget(self._label)
        self.layout().addWidget(self._assetversion_selector)

    def post_build(self):
        """Perform post-construction operations."""
        self._assetversion_selector.assetsAdded.connect(self._on_assets_added)
        self._assetversion_selector.versionChanged.connect(
            self._on_version_changed_callback
        )
        # set context
        self.set_context()

    def set_context(self):
        self._assetversion_selector.reload()

    def _on_fetch_assets_callback(self):
        '''Return assets back to asset selector'''
        # TODO: To be moved to a plugin when ui_hook is implemented
        context_id = self.context_id

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                self.plugin_config['options'].get('asset_type_name')
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
        return sorted(
            list(assets),
            key=lambda a: a['latest_version']['date'],
            reverse=True,
        )

    def _on_fetch_assetversions_callback(self, asset_entity):
        '''Query ftrack for all version beneath *asset_entity*'''
        # TODO: To be moved to a plugin when ui_hook is implemented
        result = []
        for version in self.session.query(
            'select version, id '
            'from AssetVersion where task.id is {} and asset_id is {} order by'
            ' version descending'.format(self.context_id, asset_entity['id'])
        ).all():
            result.append(version)
        return result

    def _on_assets_added(self, assets):
        if len(assets or []) > 0:
            self._label.setText(
                'We found {} asset{} published '
                ' on this task. Choose version '
                'to open'.format(
                    len(assets),
                    's' if len(assets) > 1 else '',
                )
            )
        else:
            self._label.setText('No assets found!')

    def _on_version_changed_callback(self, assetversion_entity):
        component_name = self.group_config.get('options').get('component')
        self.set_plugin_option(
            'asset_versions',
            [
                {
                    'asset_version_id': assetversion_entity['id'],
                    'component_name': component_name,
                }
            ],
        )

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
