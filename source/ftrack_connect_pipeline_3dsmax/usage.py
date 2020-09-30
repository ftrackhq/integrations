# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import ftrack_connect_pipeline_3dsmax
import ftrack_application_launcher.usage


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            # TODO(spetterborg) fix this
            # <string>sysinfo.getCommandLine() Maybe parse this?
            # 'maya_version': maya.cmds.about(v=True),

            # 2019.1+ systemTools.GetOSVersion()
            # -2017 systemTools.IsWindows98or2000()
            # -2017 systemTools.IsWindows9x()
            # 'operating_system': maya.cmds.about(os=True),
            'ftrack_connect_pipeline_3dsmax_version': ftrack_connect_pipeline_3dsmax.__version__
        }

    ftrack_application_launcher.usage.send_event(
        event_name, metadata
    )
