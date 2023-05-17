python_sources(
    name="3dsmax_project",
    sources=["**/*.py"],
    dependencies=["projects/framework-3dsmax/resource/definitions:definitions"]
)
resource(
    name="README",
    source="README.md"
)


python_distribution(
    name="framework_3dsmax",
    dependencies=[
         ":3dsmax_project",
         ":README"
    ],
    provides=python_artifact(
        name="framework_3dsmax",
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)