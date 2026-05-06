//Maya ASCII 2025 scene
//Name: empty_scene.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode transform -s -n "top";
createNode camera -s -n "topShape" -p "top";
createNode transform -s -n "front";
createNode camera -s -n "frontShape" -p "front";
createNode transform -s -n "side";
createNode camera -s -n "sideShape" -p "side";
// End of empty_scene.ma
