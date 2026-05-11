//Maya ASCII 2025 scene
//Name: shot_010.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
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
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode shadingEngine -n "metal_SG";
createNode lambert -n "metal_MAT";
createNode file -n "metal_diffuse_tex";
	setAttr ".fileTextureName" -type "string" "../shared/metal_diffuse.exr";
createNode AlembicNode -n "fx_particles";
	setAttr ".abc_File" -type "string" "particles_v001.abc";
createNode audio -n "ambience_track";
	setAttr ".filename" -type "string" "ambience.wav";
createNode reference -n "roomRN";
// End of shot_010.ma
