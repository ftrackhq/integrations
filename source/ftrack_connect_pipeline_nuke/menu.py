from nukescripts import panels

from ftrack_connect_pipeline_qt import constants as qt_constants


def build_menu_widgets(
    ftrack_menu, widget_launcher, widgets, event_manager, asset_list_model
):
    def wrap_asset_manager_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.asset_manager import (
            NukeAssetManagerClient,
        )

        return NukeAssetManagerClient(event_manager, asset_list_model)

    def wrap_publisher_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.publish import (
            NukePublisherClient,
        )

        return NukePublisherClient(event_manager, asset_list_model)

    globals()['ftrackWidgetLauncher'] = widget_launcher
    globals()['ftrackAssetManagerClass'] = wrap_asset_manager_class
    globals()['ftrackPublishClass'] = wrap_publisher_class

    # Register docked panels

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackAssetManagerClass'),
        'ftrack Pipeline Asset Manager',
        qt_constants.ASSET_MANAGER_WIDGET,
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackPublishClass'),
        'ftrack Pipeline Publisher',
        qt_constants.PUBLISHER_WIDGET,
    )

    for item in widgets:
        widget_name, unused_widget_class, label, image = item
        ftrack_menu.addCommand(
            label,
            '{0}.ftrackWidgetLauncher.launch("{1}")'.format(
                __name__, widget_name
            ),
        )
