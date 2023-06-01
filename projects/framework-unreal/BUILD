python_sources(
    name="unreal_project",
    sources=["**/*.py"],
    dependencies=["projects/framework-unreal/resource/definitions:definitions"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="ftrack_framework_unreal",
    dependencies=[
         ":unreal_project",
         ":README"
    ],
    provides=python_artifact(
        name="ftrack_framework_unreal",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)