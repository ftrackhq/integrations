# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import functools

import FnAssetAPI
from FnAssetAPI.ui.toolkit import QtGui
from ftrack_connect_foundry.ui import delegate
from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from ftrack_connect_nuke_studio.ui.widget.info_view import (
    InfoView as _InfoView
)


def openCreateProjectUI(*args, **kwargs):
    ''' Function to be triggered from createProject custom menu.
    '''
    import hiero
    parent = hiero.ui.mainWindow()
    ftags = []
    trackItems = args[0]
    for item in trackItems:
        if not isinstance(item, hiero.core.TrackItem):
            continue
        tags = item.tags()
        tags = [tag for tag in tags if tag.metadata().hasKey('ftrack.type')]
        ftags.append((item, tags))

    dialog = ProjectTreeDialog(
        data=ftags, parent=parent, sequence=item.sequence()
    )
    dialog.exec_()


class Delegate(delegate.Delegate):
    def __init__(self, bridge):
        super(Delegate, self).__init__(bridge)

        # Add custom nuke studio widgets to the widget mapping.
        for widgetClass in (_InfoView,):
            identifier = widgetClass.getIdentifier()

            # Bind bridge as first argument to class on instantiation.
            boundWidgetClass = functools.partial(widgetClass, self._bridge)

            # The returned callable is expected to be a class with certain
            # class methods available. Therefore, also dynamically assign
            # original class methods to wrapper.
            for name in ('getIdentifier', 'getDisplayName', 'getAttributes'):
                setattr(boundWidgetClass, name, getattr(widgetClass, name))

            self._widgetMapping[identifier] = boundWidgetClass

    def populate_ftrack(self):
        '''Populate the ftrack menu with items.

        .. note ::

            This method is using the nuke module which will not work if the
            plugin run in Hiero.

        '''
        # Inline to not break if plugin run in Hiero.
        import nuke

        mainMenu = nuke.menu('Nuke')
        ftrackMenu = mainMenu.addMenu('&ftrack')

        ftrackMenu.addSeparator()

        ftrackMenu.addCommand(
            'Info',
            'pane = nuke.getPaneFor("Properties.1");'
            'panel = nukescripts.restorePanel("{identifier}");'
            'panel.addToPane(pane)'.format(
                identifier=_InfoView.getIdentifier()
            )
        )

    def populateUI(self, uiElement, specification, context):
        super(Delegate, self).populateUI(uiElement, specification, context)

        host = FnAssetAPI.SessionManager.currentSession().getHost()
        if host and host.getIdentifier() == 'uk.co.foundry.nukestudio':
            import nuke.assetmgr
            if context.locale.isOfType(
                nuke.assetmgr.nukestudiohost.hostAdaptor.NukeStudioHostAdaptor.specifications.HieroTimelineContextMenuLocale
            ):
                data = context.locale.getData().get('event').sender.selection()
                cmd = functools.partial(openCreateProjectUI, data)
                action = QtGui.QAction(
                    QtGui.QPixmap(':icon-ftrack-box'),
                    'Export project', uiElement
                )
                action.triggered.connect(cmd)
                uiElement.addAction(action)

                self.populate_ftrack()
