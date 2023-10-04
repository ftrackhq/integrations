# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import platform
import os
import time
import logging

from ftrack_framework_photoshop.remote_connection.base import (
    BasePhotoshopRemoteConnection,
)

logger = logging.getLogger(__name__)


class UXBasePhotoshopRemoteConnection(BasePhotoshopRemoteConnection):
    '''Photoshop remote connection for UXP.'''

    def connect(self):
        '''(Override)'''

        # Store env in plugin data folder for pickup

        if platform.system() == "Darwin":
            # /Users/henriknorin/Library/Application Support/Adobe/UXP/PluginsStorage/PHSP/
            plugin_data_base = os.path.join(
                os.path.expanduser('~'),
                "Library",
                "Application Support",
                "Adobe",
                "UXP",
                "PluginsStorage",
                "PHSP",
            )
        else:
            # Windows
            # TODO: Validate this
            plugin_data_base = os.path.join(
                os.path.expanduser('~'),
                "AppData",
                "Roaming",
                "Adobe",
                "UXP",
                "PluginsStorage",
                "PHSP",
            )

        assert os.path.exists(
            plugin_data_base
        ), "Photoshop plugin data base does not exist: {}".format(
            plugin_data_base
        )

        #

        PHASE_WAIT_PLUGIN_LOAD = "wait-plugin-load"
        PHASE_WAIT_PICKUP_PLUGIN_DATA = "wait-pickup-plugin-data"
        PHASE_DONE = "done"

        phase = PHASE_WAIT_PLUGIN_LOAD
        env_path = None

        try:
            logger.info(
                "Waiting for plugin to load (data base: {})".format(
                    plugin_data_base
                )
            )
            waited = 0
            timeout_ms = 5 * 60 * 1000  # Wait for 5 mins
            while phase != PHASE_DONE:
                if waited > timeout_ms:
                    raise Exception(
                        "Timeout waiting for Photoshop plugin to load!"
                    )
                if phase == PHASE_WAIT_PLUGIN_LOAD:
                    for root, dirnames, filenames in os.walk(plugin_data_base):
                        # 24/Developer/ftrack-framework-photoshop/PluginData/env
                        for dirname in dirnames:
                            if dirname.startswith(
                                "ftrack-framework-photoshop"
                            ):
                                # Check if plugin id file is there
                                plugin_info_path = os.path.join(
                                    root,
                                    dirname,
                                    "PluginData",
                                    "info.json",
                                )
                                if os.path.exists(plugin_info_path):
                                    self.plugin_info = open(
                                        plugin_info_path, "r"
                                    ).read()
                                    logger.info(
                                        "Got plugin info: {}, removing".format(
                                            self.plugin_info
                                        )
                                    )
                                    os.remove(plugin_info_path)
                                    # Write ftrack env to plugin data
                                    env_path = os.path.join(
                                        os.path.dirname(plugin_info_path),
                                        ".env",
                                    )
                                    env_data = '\n'.join(
                                        [
                                            '{}={}'.format(k, v)
                                            for k, v in os.environ.items()
                                            if k.startswith("FTRACK")
                                        ]
                                    )
                                    logger.info(
                                        "Writing env to plugin data: {}".format(
                                            env_path
                                        )
                                    )
                                    with open(env_path, "w") as f:
                                        f.write(env_data)

                                    phase = PHASE_WAIT_PICKUP_PLUGIN_DATA
                                    logger.info(
                                        "Plugin loaded, waiting for pickup of plugin data"
                                    )
                elif phase == PHASE_WAIT_PICKUP_PLUGIN_DATA:
                    if not os.path.exists(env_path):
                        logger.info(
                            "Plugin data picked up, testing integration communication over event hub"
                        )
                        env_path = None
                        phase = PHASE_DONE
                        self.connected = True
                        break
                time.sleep(0.5)
                if waited > 0:
                    if phase == PHASE_WAIT_PLUGIN_LOAD:
                        logger.info(
                            "   Waited {}ms for plugin to load...".format(
                                waited
                            )
                        )
                    elif phase == PHASE_WAIT_PICKUP_PLUGIN_DATA:
                        logger.info(
                            "   Waited {}ms for plugin data to be picked up...".format(
                                waited
                            )
                        )
                waited += 500
        finally:
            # Cleanup
            if env_path is not None and os.path.exists(env_path):
                logger.warning(
                    "Cleaning up plugin env data: {}".format(env_path)
                )
                try:
                    os.remove(env_path)
                except Exception as e:
                    logger.warning(
                        "Failed to remove plugin env data: {}".format(e)
                    )

        self._spawn_event_listener()

        # Wait for Photoshop to get ready to receive events
        time.sleep(0.5)

        # Send a ping event to Photoshop to let it know we are ready
        self.event_manager.publish.remote_alive(self.integration_session_id)
