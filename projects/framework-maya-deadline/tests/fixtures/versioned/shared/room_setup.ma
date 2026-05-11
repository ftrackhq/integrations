//Maya ASCII 2025 scene
//Name: room_setup.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "table" -rfn "tableRN" -op "v=0;"
		 -typ "mayaAscii" "prop_table.ma";
file -r -ns "table" -dr 1 -rfn "tableRN" -op "v=0;"
		 -typ "mayaAscii" "prop_table.ma";
file -rdi 1 -ns "chair" -rfn "chairRN" -op "v=0;"
		 -typ "mayaBinary" "prop_chair.mb";
file -r -ns "chair" -dr 1 -rfn "chairRN" -op "v=0;"
		 -typ "mayaBinary" "prop_chair.mb";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode transform -n "room_GRP";
createNode mesh -n "floorShape" -p "room_GRP";
createNode mesh -n "wallShape" -p "room_GRP";
createNode reference -n "tableRN";
createNode reference -n "chairRN";
// End of room_setup.ma
