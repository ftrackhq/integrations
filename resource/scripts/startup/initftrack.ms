startup_dir = pathConfig.removePathLeaf (getSourceFileName())

sysinfo.currentdir = systemTools.getEnvVariable "3DSMAX_PLUG_IN_PATH"
-- Loading from
sysinfo.currentdir

-- Load the FtrackAssetHelperPlugin
python.ExecuteFile("ftrackMaxPlugin.py")

sysinfo.currentdir = startup_dir
-- Back to startup dir
sysinfo.currentdir

-- Initialize ftrack pipeline
python.ExecuteFile("init_ftrack_pipeline.py")
