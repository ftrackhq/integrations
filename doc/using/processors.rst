Processors
**********

Processors are automated processes which runs on top of each defined task through the config file,
in order to produce a defined output from the source material.

By default a set of ready to use processors is provided under the resource folder into the defaults.py file.


What are the processors
#######################

Processors are a plugins , which rely on nuke to work.
Each plugin will self contain all the logic, code and resources needed for the material to be produced.

How do I create a new processor
###############################
Let start having a look at an example processor, which will be creating and publishing the frames, and break it down.

.. code-block:: python

    from ftrack_connect_nuke_studio.processor import BasePlugin

    class PublishPlugin(BasePlugin):
        def __init__(self):
            name = 'processor.publish'
            super(PublishPlugin, self).__init__(name=name)

            self.defaults = {
                "OUT":{
                    'file_type': 'dpx',
                    'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createComponent;createComponent()'
                }
             }

            self.script = '${FTRACK_PROCESSOR_PLUGIN_PATH}/publish.nk'

        def manage_options(self, data):
            ''' for informational purpose only here we show the manage_input function
            '''
            data = super(PublishPlugin, self).manage_options(data)
            # define the output file sequence
            format = '.####.%s' % data['OUT']['file_type']
            name = self.name.replace('.', '_')
            tmp = tempfile.NamedTemporaryFile(suffix=format, delete=False, prefix=name)
            data['OUT']['file'] = tmp.name
            return data


    def register(registry):
        # create and register plugin instances
        plugin_publish = PublishPlugin()
        registry.add(plugin_publish)



As any other plugin, you need an interface to stick to , and the main processor module provide a BasePlugin to inherit from.

.. code-block:: python

    from ftrack_connect_nuke_studio.processor import BasePlugin


Each processor has a set of properties, which have to be filled up in order to have it working, let see them.

name
====
Uniquely identify the processor among the others.

defaults
========
A set of default set of options for the processor.

Defaults, is a dictionary which contains a reference of the nuke node in the provided script and the value it will be set to.
For example , this following example will be providing a standard start and end frame for the input node IN:

.. code-block:: python

            self.defaults = {
                "IN":{
                    'first': 1001,
                    'last': 1003
                }
             }


Each processor will have to express, as part of the defaults, the callback to be attached to the write node, which will enable it to publish to the ftrack server.

.. code-block:: python

            self.defaults = {
                "OUT":{
                    'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createComponent;createComponent()'
                }
             }


script
======
The full path to the nuke script which will be used.

How do I customize its behaviour
################################
The base plugin provide a method called manage_options, which will allow you to modify any data which will be set to the nuke script.
In this method is common to define the output path for the OUT node, so can be unique.


