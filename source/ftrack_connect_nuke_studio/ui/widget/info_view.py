# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_connect_foundry.ui.info_view


class InfoView(
    ftrack_connect_foundry.ui.info_view.InfoView
):
    '''Display information about selected entity.'''

    _kIdentifier = 'com.ftrack.information_panel'
    _kDisplayName = 'Info'
