..
    :copyright: Copyright (c) 2014 ftrack

******************************************
ftrack.connect.publish.make-web-reviewable
******************************************

The make-web-reviewable hook is triggered when publishing a new version. The
default hook will upload the selected component to cloud storage and encode it
to appropriate formats(:term:`mp4` and :term:`webm`).

Example event passed to hook::

    Event(
        topic='ftrack.connect.publish.make-web-playable',
        data=dict(
            versionId='eb16970c-5fc6-11e2-bb9a-f23c91df25eb',
            path='/path/to/file/to/use/for/component.mp4'
        )
    )

Default hook
============

.. literalinclude:: /../resource/hook/make_web_playable.py
    :language: python
