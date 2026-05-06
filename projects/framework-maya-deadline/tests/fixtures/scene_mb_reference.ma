//Maya ASCII 2025 scene
//Name: scene_mb_reference.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "heavy_model" -rfn "heavy_modelRN" -op "v=0;"
		 -typ "mayaBinary" "model.mb";
file -r -ns "heavy_model" -dr 1 -rfn "heavy_modelRN" -op "v=0;"
		 -typ "mayaBinary" "model.mb";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode reference -n "heavy_modelRN";
// End of scene_mb_reference.ma
