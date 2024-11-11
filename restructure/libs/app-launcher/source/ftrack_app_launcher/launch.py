# This is the actual tool

# query all yaml files and read them
# discover all the applications based on the yaml files and register the event if its called from connect
# Subscrive to the launch event on all the yaml files if its called from connect
# othewise just call the launch function directly


# By default it comes with some yaml files of apps to be launched
# User can install extensions to provide "overrides" that augment the yaml file, (See the maya-launch.yaml in the extensions folder)
# the launcher will then execute the final yaml file and it will be "inteligent" if the integration key is provided it will build the environment, downloaded the extensions, install the dependnecies.
# Then it will read the pre-launch-hook: wich is a script provider by the user (Or we provide a default one with a passthrough ))
# The pre-launch-hook is basically a way to inject things on our default launch options (We will provide the launcher, executable and environment variables as arguments or similar) and you do what you want but alwys return a valid dictionary.
# We setup all the environment variables based on the result of the pre-launch-hook
# we execute the app process with the provided envrionmets.
# launch-hook: launch_app # This is an optional key that overrides the default behaviour of how we launch the application.
