# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2019 ftrack

import logging

import ftrack_api

from ftrack_connect_pipeline_3dsmax import host as max_host
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants

from pymxs import runtime as rt
from ftrack_connect_pipeline_3dsmax import menu as ftrack_menu_module
import uuid

from ftrack_connect_pipeline.configure_logging import configure_logging
configure_logging(
    'ftrack_connect_pipeline_3dsmax',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt']
)

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax')

def initialise():

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )
    
    max_host.MaxHost(event_manager)

    from ftrack_connect_pipeline_3dsmax.client import load
    from ftrack_connect_pipeline_3dsmax.client import publish
    from ftrack_connect_pipeline_3dsmax.client import asset_manager
    from ftrack_connect_pipeline_3dsmax.client import log_viewer

    # Enable loader and publisher only if is set to run local (default)
    dialogs = []

    dialogs.append(
        (load.MaxLoaderClient, 'Loader')
    )
    dialogs.append(
        (publish.MaxPublisherClient, 'Publisher')
    )
    dialogs.append(
        (asset_manager.MaxAssetManagerClient, 'AssetManager')
    )
    dialogs.append(
        (log_viewer.MaxLogViewerClient, 'LogViewer')
    )

    menu_name = 'ftrack'
    submenu_name = 'pipeline'

    if rt.menuMan.findMenu(menu_name):
        menu = rt.menuMan.findMenu(menu_name)
        rt.menuMan.unRegisterMenu(menu)

    main_menu_bar = rt.menuMan.getMainMenuBar()
    ftrack_menu = rt.menuMan.createMenu(menu_name)
    pipeline_menu = rt.menuMan.createMenu(submenu_name)

    # Register and hook the dialog in ftrack menu
    i = 0
    for item in dialogs:
        if item == 'divider':
            pipeline_menu.addItem(rt.menuMan.createSeparatorItem(), -1)
            continue

        dialog_class, label = item

        storage_id = str(uuid.uuid4())
        ftrack_menu_module.event_manager_storage[storage_id] = event_manager
        ftrack_menu_module.dialog_class_storage[storage_id] = dialog_class

        macro_name = label
        category = "ftrack"

        # The createActionItem expects a macro and not an script.
        python_code = "\n".join(
            [
                "from ftrack_connect_pipeline_3dsmax.menu import OpenDialog",
                "open_dialog_class = OpenDialog()",
                "open_dialog_class.open_dialog('{}')".format(
                    storage_id
                )
            ]
        )
        rt.execute(
            """
            macroScript {macro_name}
            category: "{category}"
            (
                on execute do
                (
                    python.execute "{p_code}"
                )
            )
        """.format(
                macro_name=macro_name,
                category=category,
                p_code=python_code
            )
        )

        pipeline_menu.addItem(
            rt.menuMan.createActionItem(macro_name, category),
            -1
        )
        i += 1

    sub_menu_pipeline_item = rt.menuMan.createSubMenuItem(
        submenu_name, pipeline_menu
    )
    sub_menu_pipeline_index = ftrack_menu.numItems() - 1
    ftrack_menu.addItem(sub_menu_pipeline_item, sub_menu_pipeline_index)

    sub_menu_ftrack_item = rt.menuMan.createSubMenuItem(menu_name, ftrack_menu)
    sub_menu_ftrack_index = main_menu_bar.numItems() - 1
    main_menu_bar.addItem(sub_menu_ftrack_item, sub_menu_ftrack_index)

    rt.menuMan.updateMenuBar()


initialise()
