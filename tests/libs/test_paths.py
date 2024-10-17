def test__get_temp_path__file_exists() -> None:
    """Tests the existence of a file created by the get_temp_path function."""
    import os
    from ftrack_utils.paths import get_temp_path

    temp_file: str = get_temp_path()
    assert os.path.exists(temp_file) and os.path.isfile(temp_file)

    temp_file_with_extension: str = get_temp_path(filename_extension=".txt")
    assert os.path.exists(temp_file_with_extension) and os.path.isfile(
        temp_file_with_extension
    )


def test__get_temp_path__directory_exists() -> None:
    """Tests the existence of a directory created by the get_temp_path function."""
    import os
    from ftrack_utils.paths import get_temp_path

    temp_directory: str = get_temp_path(is_directory=True)
    assert os.path.exists(temp_directory) and os.path.isdir(temp_directory)

    temp_directory_with_extension: str = get_temp_path(
        is_directory=True, filename_extension=".txt"
    )
    assert os.path.exists(temp_directory) and os.path.isdir(
        temp_directory_with_extension
    )
