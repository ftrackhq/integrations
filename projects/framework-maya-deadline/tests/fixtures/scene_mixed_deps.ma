//Maya ASCII 2025 scene
//Name: scene_mixed_deps.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
requires "AbcImport" "1.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "character" -rfn "characterRN" -op "v=0;"
		 -typ "mayaAscii" "referenced_scene.ma";
file -r -ns "character" -dr 1 -rfn "characterRN" -op "v=0;"
		 -typ "mayaAscii" "referenced_scene.ma";
file -rdi 1 -ns "prop" -rfn "propRN" -op "v=0;"
		 -typ "mayaAscii" "scene_with_textures.ma";
file -r -ns "prop" -dr 1 -rfn "propRN" -op "v=0;"
		 -typ "mayaAscii" "scene_with_textures.ma";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode file -n "env_hdri_tex";
	setAttr ".fileTextureName" -type "string" "/textures/env/studio_hdri.exr";
createNode file -n "ground_color_tex";
	setAttr ".fileTextureName" -type "string" "/textures/env/ground_color.exr";
createNode file -n "ground_disp_tex";
	setAttr ".fileTextureName" -type "string" "/textures/env/ground_displacement.<UDIM>.exr";
createNode AlembicNode -n "anim_cache";
	setAttr ".abc_File" -type "string" "/cache/anim/shot010_v003.abc";
createNode audio -n "dialogue_track";
	setAttr ".filename" -type "string" "/audio/shot010_dialogue.wav";
createNode reference -n "characterRN";
createNode reference -n "propRN";
// End of scene_mixed_deps.ma
