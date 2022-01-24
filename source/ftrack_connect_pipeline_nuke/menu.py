from nukescripts import panels


def build_menu_widgets(ftrack_menu, event_manager):
    def wrap_open_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.open import NukeOpenDialog

        return NukeOpenDialog(event_manager)

    def wrap_loader_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.load import NukeLoaderClient

        return NukeLoaderClient(event_manager)

    def wrap_publisher_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.publish import NukePublisherClient

        return NukePublisherClient(event_manager)

    def wrap_asset_manager_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.asset_manager import (
            NukeAssetManagerClient,
        )

        return NukeAssetManagerClient(event_manager)

    def wrap_log_viewer_class(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.log_viewer import NukeLogViewerClient

        return NukeLogViewerClient(event_manager)

    globals()['ftrackOpenClass'] = wrap_open_class
    globals()['ftrackLoadClass'] = wrap_loader_class
    globals()['ftrackAssetManagerClass'] = wrap_asset_manager_class
    globals()['ftrackPublishClass'] = wrap_publisher_class
    globals()['ftrackLogViewerClass'] = wrap_log_viewer_class

    # Register docked panels
    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackLoadClass'),
        'ftrack Pipeline Loader',
        'QtPipelineNukeLoaderWidget',
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackAssetManagerClass'),
        'ftrack Pipeline Asset Manager',
        'QtPipelineNukeAssetManagerWidget',
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackPublishClass'),
        'ftrack Pipeline Publisher',
        'QtPipelineNukePublisherWidget',
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackLogViewerClass'),
        'ftrack Pipeline Log Manager',
        'QtPipelineNukeLogViewerWidget',
    )

    # Add menu commands
    ftrack_menu.addCommand(
        'ftrack Open', 'cls={0}.{1};' 'cls().show()'.format(__name__, 'ftrackOpenClass')
    )

    ftrack_menu.addCommand(
        'ftrack Loader',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeLoaderWidget");'
        'panel.addToPane(pane)',
    )

    ftrack_menu.addCommand(
        'ftrack Asset Manager',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeAssetManagerWidget");'
        'panel.addToPane(pane)',
    )

    ftrack_menu.addCommand(
        'ftrack Publisher',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukePublisherWidget");'
        'panel.addToPane(pane)',
    )

    ftrack_menu.addCommand(
        'ftrack Log Viewer',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeLogViewerWidget");'
        'panel.addToPane(pane)',
    )
