from nukescripts import panels

from ftrack_connect_pipeline import constants as core_constants


def build_menu_widgets(
    ftrack_menu,
    widget_launcher,
    widgets,
    event_manager,
    asset_list_model,
    created_widgets,
):
    def wrap_asset_manager_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.asset_manager import (
            NukeQtAssetManagerClientWidget,
        )

        widget = NukeQtAssetManagerClientWidget(
            event_manager, asset_list_model
        )
        created_widgets[core_constants.ASSET_MANAGER] = widget
        return widget

    def wrap_publisher_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.publish import (
            NukeQtPublisherClientWidget,
        )

        widget = NukeQtPublisherClientWidget(event_manager)
        created_widgets[core_constants.PUBLISHER] = widget
        return widget

    globals()['ftrackWidgetLauncher'] = widget_launcher
    globals()['ftrackAssetManagerClass'] = wrap_asset_manager_class
    globals()['ftrackPublishClass'] = wrap_publisher_class

    # Register docked panels

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackAssetManagerClass'),
        'ftrack Pipeline Asset Manager',
        core_constants.ASSET_MANAGER,
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackPublishClass'),
        'ftrack Pipeline Publisher',
        core_constants.PUBLISHER,
    )

    for item in widgets:
        widget_name, unused_widget_class, label, image = item
        ftrack_menu.addCommand(
            label,
            '{0}.ftrackWidgetLauncher.launch("{1}")'.format(
                __name__, widget_name
            ),
        )
