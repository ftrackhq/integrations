# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import sys
import subprocess
import glob

import unreal

### SEQUENCER/RENDER ###


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequence assets used in level. If *as_names* is True, the asset name will be used instead of the asset itself.
    '''
    result = []
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.static_class() == unreal.LevelSequenceActor.static_class():
            level_sequence = actor.load_sequence()
            value = level_sequence.get_name() if as_names else level_sequence
            if not value in result:
                result.append(value)
            break
    return result


def get_selected_sequence():
    '''Return the selected level sequence asset or None if no sequence is selected.'''
    for (
        sequence_actor
    ) in unreal.EditorLevelLibrary.get_selected_level_actors():
        if (
            sequence_actor.static_class()
            == unreal.LevelSequenceActor.static_class()
        ):
            return sequence_actor.load_sequence()
    return None


def get_sequence_shots(level_sequence):
    '''
    Returns a list of all shot tracks in the given *level_sequence*.
    '''
    result = []
    master_tracks = level_sequence.get_master_tracks()
    if master_tracks:
        for track in master_tracks:
            if (
                track.static_class()
                == unreal.MovieSceneCinematicShotTrack.static_class()
            ):
                for shot_track in track.get_sections():
                    if (
                        shot_track.static_class()
                        == unreal.MovieSceneCinematicShotSection.static_class()
                    ):
                        result.append(shot_track)

    return result


### RENDERING ###


def compile_capture_args(options):
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


def render(
    sequence_path,
    unreal_map_path,
    content_name,
    destination_path,
    fps,
    capture_args,
    logger,
    image_format=None,
    frame=None,
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
    :return:
    '''

    def __generate_target_file_path(
        destination_path, content_name, image_format, frame
    ):
        '''Generate the output file path based on *destination_path* and *content_name*'''
        # Sequencer can only render to avi file format
        if image_format is None:
            output_filename = '{}.avi'.format(content_name)
        else:
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

    def __build_process_args(
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
            unreal.SystemLibrary.get_project_directory(),
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
        cmdline_args.append("-MovieFrameRate=" + str(fps))
        if frame is not None:
            cmdline_args.append("-MovieStartFrame={}".format(frame))
            cmdline_args.append("-MovieEndFrame={}".format(frame))
        cmdline_args.extend(capture_args)
        cmdline_args.append("-NoTextureStreaming")
        cmdline_args.append("-NoLoadingScreen")
        cmdline_args.append("-NoScreenMessages")
        return cmdline_args

    try:
        # Check if any existing files
        if os.path.exists(destination_path) and os.path.isfile(
            destination_path
        ):
            logger.warning(
                'Removing existing destination file: "{}"'.format(
                    destination_path
                )
            )
            os.remove(destination_path)
        if os.path.exists(destination_path):
            for fn in os.listdir(destination_path):
                # Remove files having the same prefix as destination file
                if fn.split('.')[0] == content_name:
                    file_path = os.path.join(destination_path, fn)
                    logger.warning(
                        'Removing existing file: "{}"'.format(file_path)
                    )
                    os.remove(file_path)
        else:
            # Create it
            logger.info(
                'Creating output folder: "{}"'.format(destination_path)
            )
            os.makedirs(destination_path)
    except Exception as e:
        logger.exception(e)
        msg = (
            'Could not delete {} contents. The Sequencer will not be able to'
            ' exporters the media to that location.'.format(destination_path)
        )
        logger.error(msg)
        return False, {'message': msg}

    output_filepath = __generate_target_file_path(
        destination_path, content_name, image_format, frame
    )

    # Unreal will be started in game mode to render the video
    cmdline_args = __build_process_args(
        sequence_path,
        unreal_map_path,
        content_name,
        destination_path,
        fps,
        image_format,
        capture_args,
        frame,
    )

    logger.info('Sequencer command-line arguments: {}'.format(cmdline_args))

    # Send the arguments as a single string because some arguments could
    # contain spaces and we don't want those to be quoted
    envs = os.environ.copy()
    envs.update({'FTRACK_CONNECT_DISABLE_INTEGRATION_LOAD': '1'})
    subprocess.call(' '.join(cmdline_args), env=envs)

    return output_filepath


def find_rendered_media(render_folder, shot_name):
    '''Find rendered media in the given *render_folder*, will return a tuple with image sequence and video file if found.
    Otherwise it will return an error message'''

    error_message = 'Render folder does not exist: "{}"'.format(render_folder)

    if render_folder and os.path.exists(render_folder):

        shot_render_folder = os.path.join(render_folder, shot_name)

        error_message = 'Shot folder does not exist: "{}"'.format(
            shot_render_folder
        )

        if shot_render_folder and os.path.exists(shot_render_folder):

            error_message = 'No media found in shot folder: "{}"'.format(
                shot_render_folder
            )

            # Locate AVI media and possible image sequence on disk
            movie_path = find_movie(shot_render_folder)
            sequence_path, start, end = find_image_sequence(shot_render_folder)

            if movie_path or sequence_path:
                return movie_path, sequence_path, start, end

    return error_message


def find_image_sequence(render_folder):
    '''Try to find a continous image sequence in the *render_folder*, Unreal always names frames "Image.0001.png".
    Will return the clique parsable expression together with first and last frame number.'''

    if not render_folder or not os.path.exists(render_folder):
        return None, -1, -1

    # Search folder for images sequence, extract minimum and maximum frame number
    prefix = None
    ext = None
    start = sys.maxsize
    end = -sys.maxsize
    for filename in os.listdir(render_folder):
        parts = filename.split('.')
        if len(parts) == 3:
            if prefix is None:
                prefix = parts[0]
            elif prefix != parts[0]:
                continue  # Ignore files with different prefix
            if ext is None:
                ext = parts[2]
            elif ext != parts[2]:
                continue  # Ignore files with different extension
            try:
                frame = int(parts[1])
                if frame < start:
                    start = frame
                if frame > end:
                    end = frame
            except:
                continue
    return (
        '{}.%04d.{} [{}-{}]'.format(
            os.path.join(render_folder, prefix),
            ext,
            start,
            end,
        ),
        start,
        end,
    )


def find_movie(render_folder):
    if not render_folder or not os.path.exists(render_folder):
        return None

    avi_files = glob.glob(os.path.join(render_folder, '*.avi'))

    if avi_files:
        return avi_files[0]

    return None
