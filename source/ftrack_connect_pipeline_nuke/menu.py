from nukescripts import panels


def build_menu_widgets(ftrack_menu, hostid):

    def wrap_publisher(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.publish import QtPipelineNukePublisherWidget
        return QtPipelineNukePublisherWidget(hostid)

    def wrap_loader(*args, **kwargs):
        from ftrack_connect_pipeline_nuke.client.load import QtPipelineNukeLoaderWidget
        return QtPipelineNukeLoaderWidget(hostid)

    globals()['ftrackPublishClass'] = wrap_publisher
    globals()['ftrackLoadClass'] = wrap_loader

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

