//Maya ASCII 2025 scene
//Name: scene_with_reference.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "character" -rfn "characterRN" -op "v=0;"
		 -typ "mayaAscii" "referenced_scene.ma";
file -r -ns "character" -dr 1 -rfn "characterRN" -op "v=0;"
		 -typ "mayaAscii" "referenced_scene.ma";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode reference -n "characterRN";
// End of scene_with_reference.ma
