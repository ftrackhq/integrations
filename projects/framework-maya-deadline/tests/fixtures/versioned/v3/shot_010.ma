//Maya ASCII 2025 scene
//Name: shot_010.ma
//Last modified: Thu, May 15, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
requires "AbcImport" "1.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "room" -rfn "roomRN" -op "v=0;"
		 -typ "mayaAscii" "../shared/room_setup.ma";
file -r -ns "room" -dr 1 -rfn "roomRN" -op "v=0;"
		 -typ "mayaAscii" "../shared/room_setup.ma";
file -rdi 1 -ns "lamp" -rfn "lampRN" -op "v=0;"
		 -typ "mayaAscii" "prop_lamp.ma";
file -r -ns "lamp" -dr 1 -rfn "lampRN" -op "v=0;"
		 -typ "mayaAscii" "prop_lamp.ma";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode shadingEngine -n "metal_SG";
createNode lambert -n "metal_MAT";
createNode file -n "metal_diffuse_tex";
	setAttr ".fileTextureName" -type "string" "../shared/metal_diffuse.exr";
createNode file -n "metal_roughness_tex";
	setAttr ".fileTextureName" -type "string" "../v2/metal_roughness.exr";
createNode AlembicNode -n "fx_particles";
	setAttr ".abc_File" -type "string" "../v2/particles_v002.abc";
createNode reference -n "roomRN";
createNode reference -n "lampRN";
// End of shot_010.ma
