//Maya ASCII 2025 scene
//Name: prop_lamp.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "lamp_GRP";
createNode mesh -n "lampBaseShape" -p "lamp_GRP";
createNode mesh -n "lampShadeShape" -p "lamp_GRP";
createNode shadingEngine -n "fabric_SG";
createNode lambert -n "fabric_MAT";
createNode file -n "fabric_diffuse_tex";
	setAttr ".fileTextureName" -type "string" "fabric_diffuse.<UDIM>.exr";
createNode file -n "fabric_normal_tex";
	setAttr ".fileTextureName" -type "string" "fabric_normal.exr";
createNode place2dTexture -n "place2d_fabric_diff";
createNode place2dTexture -n "place2d_fabric_norm";
// End of prop_lamp.ma
