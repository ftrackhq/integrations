import os
import flame

_PRESETS = {
    'JPG8': {
        "visibility": flame.PyExporter.PresetVisibility.Autodesk,
        "type": flame.PyExporter.PresetType.Image_Sequence,
        "dir": "Jpeg",
        "preset": "Jpeg (8-bit).xml",
    },
    'MOV8': {
        "visibility": flame.PyExporter.PresetVisibility.Autodesk,
        "type": flame.PyExporter.PresetType.Movie,
        "dir": "QuickTime",
        "preset": "QuickTime (8-bit Uncompressed).xml",
    }
}



def get_preset_path(preset_name):
    preset = _PRESETS.get(preset_name)
    if not preset:
        return

    preset_dir = flame.PyExporter.get_presets_dir(
        preset["visib"], preset["type"]
    )

    preset_path = os.path.join(
        preset_dir, preset["dir"], preset["preset"]
    )

    return preset_path