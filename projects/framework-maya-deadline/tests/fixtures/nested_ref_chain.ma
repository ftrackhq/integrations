//Maya ASCII 2025 scene
//Name: nested_ref_chain.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "shot_layout" -rfn "shot_layoutRN" -op "v=0;"
		 -typ "mayaAscii" "scene_with_reference.ma";
file -r -ns "shot_layout" -dr 1 -rfn "shot_layoutRN" -op "v=0;"
		 -typ "mayaAscii" "scene_with_reference.ma";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode reference -n "shot_layoutRN";
// End of nested_ref_chain.ma
