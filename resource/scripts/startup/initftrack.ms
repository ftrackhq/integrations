sysinfo.currentdir = systemTools.getEnvVariable "3DSMAX_PLUG_IN_PATH"
-- Loading from
sysinfo.currentdir
-- Load the FtrackAssetHelperPlugin
include "ftrackMaxPlugin.ms"

python.ExecuteFile("init_ftrack_pipeline.py")
