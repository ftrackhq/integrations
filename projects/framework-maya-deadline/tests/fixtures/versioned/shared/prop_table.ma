//Maya ASCII 2025 scene
//Name: prop_table.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "table_GRP";
createNode mesh -n "tableTopShape" -p "table_GRP";
createNode mesh -n "tableLegShape" -p "table_GRP";
createNode shadingEngine -n "wood_SG";
createNode lambert -n "wood_MAT";
createNode file -n "wood_diffuse_tex";
	setAttr ".fileTextureName" -type "string" "wood_diffuse.exr";
createNode file -n "wood_normal_tex";
	setAttr ".fileTextureName" -type "string" "wood_normal.exr";
createNode place2dTexture -n "place2d_wood_diff";
createNode place2dTexture -n "place2d_wood_norm";
// End of prop_table.ma
