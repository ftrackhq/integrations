from nukescripts import panels


def build_menu_widgets(ftrack_menu, event_manager):

    def wrap_publisher(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.publish import NukePublisherClient
        return NukePublisherClient(event_manager)

    def wrap_loader(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.load import NukeLoaderClient
        return NukeLoaderClient(event_manager)

    def wrap_asset_manager(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.asset_manager import NukeAssetManagerClient
        return NukeAssetManagerClient(event_manager)

    def wrap_log_viewer(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.log_viewer import NukeLogViewerClient
        return NukeLogViewerClient(event_manager)

    globals()['ftrackPublishClass'] = wrap_publisher
    globals()['ftrackLoadClass'] = wrap_loader
    globals()['ftrackAssetManagerClass'] = wrap_asset_manager
    globals()['ftrackLogViewerClass'] = wrap_log_viewer

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackPublishClass'),
        'Ftrack Pipeline Publisher',
        'QtPipelineNukePublisherWidget'
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackLoadClass'),
        'Ftrack Pipeline Loader',
        'QtPipelineNukeLoaderWidget'
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackAssetManagerClass'),
        'Ftrack Pipeline Asset Manager',
        'QtPipelineNukeAssetManagerWidget'
    )

    panels.registerWidgetAsPanel(
        '{0}.{1}'.format(__name__, 'ftrackLogViewerClass'),
        'Ftrack Pipeline Log Manager',
        'QtPipelineNukeLogViewerWidget'
    )

    ftrack_menu.addCommand(
        'Ftrack Publisher',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukePublisherWidget");'
        'panel.addToPane(pane)'
    )

    ftrack_menu.addCommand(
        'Ftrack Loader',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeLoaderWidget");'
        'panel.addToPane(pane)'
    )

    ftrack_menu.addCommand(
        'Ftrack Asset Manager',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeAssetManagerWidget");'
        'panel.addToPane(pane)'
    )

    ftrack_menu.addCommand(
        'Ftrack Log Viewer',
        'pane = nuke.getPaneFor("Properties.1");'
        'panel = nukescripts.restorePanel("QtPipelineNukeLogViewerWidget");'
        'panel.addToPane(pane)'
    )

