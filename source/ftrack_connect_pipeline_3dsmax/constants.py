HOST = '3dsmax'
UI = '3dsmax'


#ftrack node
import MaxPlus

FTRACK_ASSET_HELPER_CLASS_ID = MaxPlus.Class_ID(0x5c8d275e, 0x677d591c)

#Load Modes
IMPORT_MODE = 'Import'
OBJECT_XREF_MODE = 'Object XRef'
SCENE_XREF_MODE = 'Scene XRef'
OPEN_MODE = 'Open'

#Legacy Parameters Mapping
LEGACY_PARAMETERS_MAPPING = {
    'assetId':'version_id',
    'assetVersion':'version_number',
    'assetPath':'component_path',
    'assetTake':'component_name',
    'assetType':'asset_type',
    'assetComponentId':'component_id',
    'assetImportMode':'asset_load_mode'

}