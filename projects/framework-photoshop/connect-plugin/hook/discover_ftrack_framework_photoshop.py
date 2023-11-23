# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import platform
import os
import sys
import ftrack_api
import logging
import functools
import uuid
import subprocess

from ftrack_connect.util import get_connect_plugin_version

NAME = 'framework-photoshop'
''' The name of the integration, should match name in bootstrap and launcher'''

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

python_dependencies = os.path.join(connect_plugin_path, 'dependencies')


def on_discover_pipeline_photoshop(session, event):
    data = {
        'integration': {
            'name': NAME,
            'version': __version__,
        }
    }

    return data


def on_launch_pipeline_photoshop(session, event):
    '''Handle application launch and add environment to *event*.'''

    pipeline_photoshop_base_data = {
        'integration': event['data']['integration']
    }

    discover_data = on_discover_pipeline_photoshop(session, event)
    for key in discover_data['integration']:
        pipeline_photoshop_base_data['integration'][key] = discover_data[
            'integration'
        ][key]

    photoshop_version = event['data']['application']['version'].version[0]

    use_uxp = (os.environ.get('FTRACK_PHOTOSHOP_UXP') or '').lower() in [
        'true',
        '1',
    ]

    if use_uxp:
        # UXP
        if not (
            os.environ.get('FTRACK_PHOTOSHOP_UXP_AUTOINSTALL_DISABLE') or ''
        ).lower() in ['true', '1']:
            update_uxp_plugin()
        else:
            logger.warning('UXP plugin install disabled!')
    else:
        # CEP plugin, requires to be manually installed in Photoshop, integration will
        # check for its existence.
        pass

    if not pipeline_photoshop_base_data['integration'].get('env'):
        pipeline_photoshop_base_data['integration']['env'] = {}

    pipeline_photoshop_base_data['integration']['env'][
        'PYTHONPATH.prepend'
    ] = os.path.pathsep.join([python_dependencies])
    pipeline_photoshop_base_data['integration']['env'][
        'FTRACK_INTEGRATION_SESSION_ID'
    ] = uuid.uuid4().hex
    pipeline_photoshop_base_data['integration']['env'][
        'FTRACK_PHOTOSHOP_VERSION'
    ] = str(photoshop_version)

    if not use_uxp and sys.platform == 'darwin':
        # Check if running on apple silicon (arm64)
        if (
            subprocess.check_output("arch").decode('utf-8').find('i386') == -1
            or True
        ):
            logger.warning(
                'Running on non Intel hardware(Apple Silicon), will require PS '
                'to be launched in Rosetta mode!'
            )
            pipeline_photoshop_base_data['integration']['env'][
                'FTRACK_LAUNCH_ARCH'
            ] = 'x86_64'

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        pipeline_photoshop_base_data['integration']['env'][
            'FTRACK_CONTEXTID.set'
        ] = task['id']
        parent = session.query(
            'select custom_attributes from Context where id={}'.format(
                task['parent']['id']
            )
        ).first()  # Make sure updated custom attributes are fetched
        pipeline_photoshop_base_data['integration']['env']['FS.set'] = parent[
            'custom_attributes'
        ].get('fstart', '1.0')
        pipeline_photoshop_base_data['integration']['env']['FE.set'] = parent[
            'custom_attributes'
        ].get('fend', '100.0')
        pipeline_photoshop_base_data['integration']['env']['FPS.set'] = parent[
            'custom_attributes'
        ].get('fps', '24.0')

    return pipeline_photoshop_base_data


def update_uxp_plugin():
    '''Install or update the UXP plugin'''

    from ftrack_framework_photoshop import (
        __version__ as integration_version,
    )

    path_plugin_base = os.path.join(
        connect_plugin_path, 'resource', 'plugins', 'photoshop', 'uxp'
    )

    if platform.system() == 'Darwin':
        path_uxp_tool = (
            "/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents/UPI/"
            "UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app/Contents/MacOS/"
            "UnifiedPluginInstallerAgent"
        )
        if not os.path.exists(path_uxp_tool):
            logger.warning(
                "Could not find UXP tool @ {}, required for installing UXP plugin.".format(
                    path_uxp_tool
                )
            )
            return
        output = subprocess.check_output(
            [path_uxp_tool, "--list", "all"]
        ).decode("utf-8")
    else:
        # TODO: Update for Windows
        raise Exception(
            "Platform {} not supported yet".format(platform.system())
        )

    # Expect:
    # Status                        Extension Name                         Version

    # =========  =======================================================  ==========

    # 1 extension installed for Photoshop 2023 (ver 24.5.0)
    # Status                        Extension Name                         Version
    # =========  =======================================================  ==========
    # Enabled    ftrack Photoshop integration                                 0.1.0
    # ..

    found_version = None
    for line in output.split("\n"):
        if line.find('ftrack') > -1:
            found_version = line.split(" ")[-1]
            break

    logger.info(
        "Found installed plugin version: {} (current: {})".format(
            found_version, integration_version
        )
    )

    if not found_version or found_version != integration_version:
        if found_version:
            # Uninstall previous version
            logger.info("Uninstalling previous version")
            p = subprocess.run(
                [path_uxp_tool, "--remove", "ftrack Photoshop integration"]
            )
            if p.returncode != 0:
                raise Exception(
                    "Failed to uninstall previous photoshop plugin version!"
                )

        # Find plugin
        logger.info("Finding packaged plugin @ {}".format(path_plugin_base))
        plugin_package = None
        for filename in os.listdir(path_plugin_base):
            if filename.endswith(".ccx"):
                plugin_package = os.path.join(path_plugin_base, filename)
                break

        # Install plugin
        logger.info("Installing version {}".format(integration_version))
        p = subprocess.run([path_uxp_tool, "--install", plugin_package])
        if p.returncode != 0:
            raise Exception("Failed to install photoshop plugin!")
        logger.info(
            "Successfully installed packaged plugin @ {} (v{})".format(
                path_plugin_base, integration_version
            )
        )


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_photoshop, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=photoshop*'
        ' and data.application.version >= 2014',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(
        on_launch_pipeline_photoshop, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=photoshop*'
        ' and data.application.version >= 2014',
        handle_launch_event,
        priority=40,
    )

    logger.info(
        'Registered {} integration v{} discovery and launch.'.format(
            NAME, __version__
        )
    )
