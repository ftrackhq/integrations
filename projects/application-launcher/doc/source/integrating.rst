###########
Integrating
###########

Launching an application is usually not enough to have ftrack integrated.
In order to do so , integrations are provided separately.

The purpose of this hook is to provide vital information to the application startup, so the
ftrack api and integration code can be fully loaded and put to the use.


Each integration will provide something similar to the hook below.:

 .. literalinclude:: examples/discover-integration-example.py


This discover is composed by 3 important pieces.

* 2 listeners to discover and launch
* 1 function hooked to them.


Listeners
---------

Each integration will have to provide two event listeners hooked to the same function.

Each of this will have to provide a filter for the application to be launched, optional, but suggested
is to provide a lower/higher limit based on the application version for this integration.

In case more than one integration has to be loaded in a given order is suggested to provide them with an increasing
priority version.

The discovery one::

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=an_application*'
        ' and data.application.version >= 2021',
        handle_event, priority=40
    )


The above event will be emitted during the discovery cycle of the applications , which happens when the correct context
gets selected. This is used to check the version and if the integration is available.



And the launch one::

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=an_application*'
        ' and data.application.version >= 2021',
        handle_event, priority=40
    )

The above event will be emitted during the launch cycle of the applications and will be used to parse and inject the environment
variables defined during the application's startup.

Discover Function
-----------------

The discover function will be the one to provide to the applications the right environment where to pick the required files.


The bare minimum amount of data it should return in order to be discovered as working integrations is ::


    {
        'integration': {
            "name": '<name-of-the-integration>',
            'version': '<the.integration.version>'
        }
    }

where a fully formed integrations would provide also entry point for the environment variables::

    data = {
        'integration': {
            "name": 'ftrack-example-integration',
            'version': '0.0.0',
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': hook_path,
                'PYTHONPATH.prepend': os.path.pathsep.join([python_dependencies]),
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0')
            }
        }
    }



Managing environment variables
------------------------------

Each integration can express a set of environment variables and operations to be performed when handled by the application launcher.

the formatting of envs is composed by : **<$ENVIRONMENT>** . **<OPERATION>**

for example::

    'PYTHONPATH.append': '<some file system path>'


environment operations
......................

.. note::

    If not provided, the default operation for environment will be *append*


* **prepend** : The value of the environment will be prepended.
* **append** : The value of the environment will be appended.
* **set**: The given environment will be set with the given value.
* **pop**: The value of the environment variable will be removed.
* **unset**: The environment value will be unset.


.. note::
    In case of multiple integrations loaded, the priority provided in the integration will drive the order the environment variables will be manipulated.


