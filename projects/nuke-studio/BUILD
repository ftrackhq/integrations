python_sources(
    name="nuke_studio_project",
    sources=["**/*.py"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="ftrack_nuke_studio",
    dependencies=[
         ":nuke_studio_project",
         ":README",
         "projects/nuke-studio/resource:qt_style"
    ],
    provides=python_artifact(
        name="ftrack_nuke_studio",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)