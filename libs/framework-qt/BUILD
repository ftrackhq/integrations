python_sources(
    name="qt_lib",
    sources=["**/*.py"],
    #dependencies=["libs/framework-qt/resource/definitions:definitions"]
)
resource(
    name="README",
    source="README.md"
)

python_distribution(
    name="framework_qt",
    dependencies=[
         ":qt_lib",
         ":README",
    ],
    provides=python_artifact(
        name="framework_qt",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)