python_sources(
    name="lib",
    sources=["**/*.py"],#, "!doc/*", "!test/*"],
    dependencies=["libs/framework-core/resource/definitions:definitions"]
)
resource(
    name="README",
    source="README.md"
)

python_distribution(
    name="framework_core",
    dependencies=[
         ":lib",
         ":README",
        # Dependencies on code to be packaged into the distribution.
    ],
    provides=python_artifact(
        name="framework_core",
        # version="2.21.0", # No need as we use the given by setup.py
    ),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39"]},
    generate_setup = False,
)