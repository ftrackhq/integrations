startup_dir = pathConfig.removePathLeaf (getSourceFileName())

sysinfo.currentdir = systemTools.getEnvVariable "3DSMAX_PLUG_IN_PATH"

-- Load the FtrackAssetHelperPlugin
python.ExecuteFile(sysinfo.currentdir+"\ftrackMaxPlugin.py")

sysinfo.currentdir = startup_dir
-- Back to startup dir
sysinfo.currentdir

-- Initialize ftrack pipeline
python.ExecuteFile(sysinfo.currentdir+"\init_ftrack_pipeline.py")
