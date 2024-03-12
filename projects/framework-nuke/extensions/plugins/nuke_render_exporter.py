# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import traceback
import nuke

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class NukePlayblastExporterPlugin(BasePlugin):
    name = 'nuke_render_exporter'

    def run(self, store):
        '''
        Render a movie from the selected write node given in the *store*.
        Save it to a temp file and this one will be published as reviewable.
        '''
        component_name = self.options.get('component')
        node_name = store['components'][component_name].get('node_name')

        if not node_name:
            raise PluginExecutionError(
                message="No node name provided to render."
            )

        input_node = nuke.toNode(node_name)

        # Create and render a write node and connect it to the selected input node
        write_node = None
        movie_path = get_temp_path('mov')
        try:
            write_node = nuke.createNode('Write')
            write_node.setInput(0, input_node)

            write_node['first'].setValue(
                int(float(nuke.root()['first_frame'].value()))
            )
            write_node['last'].setValue(
                int(float(nuke.root()['last_frame'].value()))
            )

            first = int(write_node['first'].getValue())
            last = int(write_node['last'].getValue())

            write_node['file'].setValue(movie_path.replace('\\', '/'))

            write_node['file_type'].setValue('mov')
            write_node['mov64_codec'].setValue('mp4v')

            self.logger.debug(
                'Rendering movie [{}-{}] to "{}"'.format(
                    first, last, movie_path
                )
            )
            nuke.render(write_node, first, last, continueOnError=True)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            raise PluginExecutionError(
                message=f"Error rendering reviewable movie. Details: {e}"
            )
        finally:
            if write_node:
                # delete temporary write node
                nuke.delete(write_node)

        store['components'][component_name]['exported_path'] = movie_path
