python_sources(
    name="qt_lib",
    sources=["**/*.py"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="ftrack_framework_qt",
    dependencies=[
         ":qt_lib",
         ":README",
         "libs/framework-qt/resource/style:qt_style"
    ],
    provides=python_artifact(
        name="ftrack_framework_qt",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)