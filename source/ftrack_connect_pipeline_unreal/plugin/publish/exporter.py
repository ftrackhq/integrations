# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import sys
import subprocess
import os

import unreal

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, UnrealBasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''

    def _generate_target_file_path(
        self, destination_path, content_name, image_format, frame, movie_format
    ):
        '''Generate the output file path based on *destination_path* and *content_name* with *image_format*, *frame* and *movie_format*.'''
        if image_format is None:
            # Render movie
            output_filename = '{}.{}'.format(content_name, movie_format)
        else:
            # Render image sequence
            if frame is None:
                output_filename = (
                    '{}'.format(content_name)
                    + '.{frame}.'
                    + '{}'.format(image_format)
                )
            else:
                output_filename = '{}.{}.{}'.format(
                    content_name, '%04d' % frame, image_format
                )
        output_filepath = os.path.join(destination_path, output_filename)
        return output_filepath

    def compile_capture_args(self, options):
        '''Compile capture Unreal capture arguments from *options*.'''
        capture_args = []
        if 'resolution' in options:
            resolution = options['resolution']  # On the form 320x240(4:3)
            parts = resolution.split('(')[0].split('x')
            capture_args.append('-ResX={}'.format(parts[0]))
            capture_args.append('-ResY={}'.format(parts[1]))
        if 'movie_quality' in options:
            quality = int(options['movie_quality'])
            capture_args.append(
                '-MovieQuality={}'.format(max(0, min(quality, 100)))
            )
        return capture_args

    def _build_process_args(
        self,
        sequence_path,
        unreal_map_path,
        content_name,
        destination_path,
        fps,
        image_format,
        capture_args,
        frame,
    ):
        '''Build unreal command line arguments based on the arguments given.'''
        # Render the sequence to a movie file using the following
        # command-line arguments
        cmdline_args = []

        # Note that any command-line arguments (usually paths) that could
        # contain spaces must be enclosed between quotes
        unreal_exec_path = '"{}"'.format(sys.executable)

        # Get the Unreal project to load
        unreal_project_filename = '{}.uproject'.format(
            unreal.SystemLibrary.get_game_name()
        )
        unreal_project_path = os.path.join(
            unreal_utils.get_project_path(),
            unreal_project_filename,
        )
        unreal_project_path = '"{}"'.format(unreal_project_path)

        # Important to keep the order for these arguments
        cmdline_args.append(unreal_exec_path)  # Unreal executable path
        cmdline_args.append(unreal_project_path)  # Unreal project
        cmdline_args.append(
            unreal_map_path
        )  # Level to load for rendering the sequence

        # Command-line arguments for Sequencer Render to Movie
        # See: https://docs.unrealengine.com/en-us/Engine/Sequencer/
        #           Workflow/RenderingCmdLine
        sequence_path = '-LevelSequence={}'.format(sequence_path)
        cmdline_args.append(sequence_path)  # The sequence to render

        output_path = '-MovieFolder="{}"'.format(destination_path)
        cmdline_args.append(
            output_path
        )  # exporters folder, must match the work template

        movie_name_arg = '-MovieName={}'.format(content_name)
        cmdline_args.append(movie_name_arg)  # exporters filename

        cmdline_args.append("-game")
        cmdline_args.append(
            '-MovieSceneCaptureType=/Script/MovieSceneCapture.'
            'AutomatedLevelSequenceCapture'
        )
        cmdline_args.append("-ForceRes")
        cmdline_args.append("-Windowed")
        cmdline_args.append("-MovieCinematicMode=yes")
        if image_format is not None:
            cmdline_args.append("-MovieFormat={}".format(image_format.upper()))
        else:
            cmdline_args.append("-MovieFormat=Video")
        cmdline_args.append("-MovieFrameRate={}".format(fps))
        if frame is not None:
            cmdline_args.append("-MovieStartFrame={}".format(frame))
            cmdline_args.append("-MovieEndFrame={}".format(frame))
        cmdline_args.extend(capture_args)
        cmdline_args.append("-NoTextureStreaming")
        cmdline_args.append("-NoLoadingScreen")
        cmdline_args.append("-NoScreenMessages")
        return cmdline_args

    def render(
        self,
        sequence_path,
        unreal_map_path,
        content_name,
        destination_path,
        fps,
        capture_args,
        logger,
        image_format=None,
        frame=None,
        movie_format='avi',
    ):
        '''
        Render a video or image sequence from the given sequence actor.

        :param sequence_path: The path of the sequence within the level.
        :param unreal_map_path: The level to render.
        :param content_name: The name of the render.
        :param destination_path: The path to render to.
        :param fps: The framerate.
        :param capture_args: White space separate list of additional capture arguments.
        :param logger: A logger to log to.
        :param image_format: (Optional) The image sequence file format, if None a video (.avi) will be rendered.
        :param frame: (Optional) The target frame to render within sequence.
        :param movie_format: (Optional) The movie format to render to, Unreal currently supports AVI only
        :return: Returns the rendered file path.
        '''

        try:
            if not os.path.exists(destination_path):
                # Create it
                logger.info(
                    'Creating output folder: "{}"'.format(destination_path)
                )
                os.makedirs(destination_path)
        except Exception as e:
            logger.exception(e)
            msg = (
                'Could not create {}. The Sequencer will not be able to'
                ' exporters the media to that location.'.format(
                    destination_path
                )
            )
            logger.error(msg)
            return [], {'message': msg}

        output_filepath = self._generate_target_file_path(
            destination_path, content_name, image_format, frame, movie_format
        )

        # Unreal will be started in game mode to render the video
        cmdline_args = self._build_process_args(
            sequence_path,
            unreal_map_path,
            content_name,
            destination_path,
            fps,
            image_format,
            capture_args,
            frame,
        )

        logger.info(
            'Sequencer command-line arguments: {}'.format(cmdline_args)
        )

        # Send the arguments as a single string because some arguments could
        # contain spaces, and we don't want those to be quoted
        envs = os.environ.copy()
        envs.update({'FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD': '1'})
        subprocess.call(' '.join(cmdline_args), env=envs)

        return output_filepath


class UnrealPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, UnrealBasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
