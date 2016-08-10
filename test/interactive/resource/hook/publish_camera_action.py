import ftrack_api

import ftrack_pyblish_prototype.pyblish_ui
import ftrack_pyblish_prototype.util
import ftrack_pyblish_prototype.widget

identifier = 'ftrack-publish-maya-camera-action'


def open_dialog():
    '''Open dialog.'''
    reload(ftrack_pyblish_prototype.pyblish_ui)
    reload(ftrack_pyblish_prototype.widget)
    dialog = ftrack_pyblish_prototype.pyblish_ui.PublishDialog(
        label='Camera',
        description=(
            'from here you can select and publish Maya cameras to ftrack.'
        ),
        instance_filter=(
            lambda instance: instance.data.get('family') in ('camera',)
        )
    )
    dialog.exec_()


def discover(event):
    '''Return action based on *event*.'''
    item = {
        'items': [{
            'label': 'Camera',
            'icon': 'http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png',
            'actionIdentifier': identifier
        }]
    }

    return item


def launch(event):
    '''Callback method for Camera publish action.'''
    ftrack_pyblish_prototype.util.invoke_in_main_thread(open_dialog)

    return {
        'success': True,
        'message': 'Camera publish action started successfully!'
    }


def register(session, **kw):
    '''Register action.'''
    if not isinstance(session, ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.action.discover',
        discover
    )

    session.event_hub.subscribe(
        'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
            identifier
        ),
        launch
    )
