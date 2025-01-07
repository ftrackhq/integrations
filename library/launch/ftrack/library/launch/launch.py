# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def launch_application(
    app_name,
    hooks,
):
    """Logic to launch the specified app."""
    # store = {"discovery-hook": [], "pre-launch-hook": [], "launch-hook": []}
    # engine = Engine(
    #     store
    # )  # The engine is an utility that lives in the ftrack utils library for example?
    # hooks_result = engine.run(hooks)

    print(f"Launching application: {app_name}")
