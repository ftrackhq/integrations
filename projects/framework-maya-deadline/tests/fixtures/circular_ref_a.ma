//Maya ASCII 2025 scene
//Name: circular_ref_a.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
file -rdi 1 -ns "other" -rfn "otherRN" -op "v=0;"
		 -typ "mayaAscii" "circular_ref_b.ma";
file -r -ns "other" -dr 1 -rfn "otherRN" -op "v=0;"
		 -typ "mayaAscii" "circular_ref_b.ma";
createNode transform -n "box_GRP";
createNode reference -n "otherRN";
// End of circular_ref_a.ma
