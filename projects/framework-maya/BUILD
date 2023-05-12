python_sources(
    name="maya_project",
    sources=["**/*.py"],
    dependencies=["projects/framework-maya/resource/definitions:definitions"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="framework_maya",
    dependencies=[
         ":maya_project",
         ":README"
    ],
    provides=python_artifact(
        name="framework_maya",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)