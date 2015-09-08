..
    :copyright: Copyright (c) 2015 ftrack

.. _developing/processors:

**********
Processors
**********

Processors in Nuke studio build upon the event system used in ftrack. As such,
each processor's discover and launch method receives a single argument which
is an instance of ftrack.Event.

The built-in processors can be extended by creating new processors and placing
them in a directory. Then configure the environment by setting the
``FTRACK_EVENT_PLUGIN_PATH`` environment variable.

The processors make use of two events ``ftrack.processor.discover`` and
``ftrack.processor.launch`` that are emitted for each object being created when
running :ref:`Export project <using/export_project>`.

ftrack.processor.discover
=========================

The discover event, ``ftrack.processor.discover``, is emitted to discover which
processors are available for a certain object.

The structure of the event is:: 

    ftrack.Event(
        topic='ftrack.processor.discover',
        data=dict(
            name='010',
            object_type='Shot'
        )
    )

To make a processor available for on all shot creations you have to subscribe 
to the event hub::
    
    def discover(event):
        '''Return processor configuration for *event*.'''
        return dict(
            defaults=dict(
                # Default values.
            ),
            name='Review',
            processor_name='processor.review',
            asset_name='BG'
        )

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.processor.discover and data.object_type=shot',
        discover
    )

The dictionary returned by the discover contains the following values:

*   **defaults** - Must be a :py:class:`dict` and is rendered in the UI to
    communicate to the end-user any defaults that will be used when running the
    processor.
*   **name** - A nice name of the processor displayed in the UI. 
*   **processor_name** - The processor name.
*   **asset_name** - An optional asset name that is used to group the processors
    in the UI. A corresponding asset version will be created based on the name.

.. image:: /image/processors.png


ftrack.processor.launch
=======================

The launch event, ``ftrack.processor.launch``, is emitted to launch the
processor when it is available on the :term:`ftrack server`.

The structure of the event is:: 

    ftrack.Event(
        topic='ftrack.processor.launch',
        data=dict(
            name='Review',
            input=data
        )
    )

Where *data* is a dictionary containing contextual about the object being
processed. The dictionary contains the following information: resolution,
source_in, source_out, source_file, destination_in, destination_out, fps,
offset, entity_id, entity_type, handles. Where entity_id and entity_type points
to the object being created in ftrack.

Optional values are:

*   **asset_version_id** - Id of the asset version created if asset_name was
    passed in the defaults dictionary when the processor was discovered.
*   **component_name** - the suggested name of the component inferred from the
    processor nice name passed in the discover event.

To make a processor launch for on all shot creations you have to subscribe 
to the event hub::

    def launch(event):
        '''Launch processor with *event*.'''
        ...


    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.processor.launch and data.name=processor.review',
        launch
    )
