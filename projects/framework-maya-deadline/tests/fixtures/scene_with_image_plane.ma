//Maya ASCII 2025 scene
//Name: scene_with_image_plane.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -s -n "persp";
createNode camera -s -n "perspShape" -p "persp";
createNode imagePlane -n "imagePlane1";
	setAttr ".imageName" -type "string" "/reference/storyboard_frame.tif";
	setAttr ".useFrameExtension" 0;
	setAttr ".depth" 100;
// End of scene_with_image_plane.ma
