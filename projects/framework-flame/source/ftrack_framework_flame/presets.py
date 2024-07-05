import flame

PRESETS = [
    {
        "visibility": flame.PyExporter.PresetVisibility.Autodesk,
        "type": flame.PyExporter.PresetType.Movie,
        "dir": "QuickTime",
        "preset": "QuickTime (8-bit Uncompressed).xml",
    },
    {
        "visibility": flame.PyExporter.PresetVisibility.Autodesk,
        "type": flame.PyExporter.PresetType.Image_Sequence,
        "dir": "Jpeg",
        "preset": "Jpeg (8-bit).xml",
    },
]