//Maya ASCII 2025 scene
//Name: scene_with_textures.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "prop_GRP";
createNode mesh -n "propShape" -p "prop_GRP";
createNode shadingEngine -n "prop_SG";
createNode lambert -n "prop_MAT";
createNode file -n "diffuse_color_tex";
	rename -uid "C3D4E5F6-A7B8-9012-CDEF-123456789012";
	setAttr ".fileTextureName" -type "string" "/textures/asset/diffuse_color.exr";
createNode file -n "displacement_tex";
	rename -uid "D4E5F6A7-B8C9-0123-DEFA-234567890123";
	setAttr ".fileTextureName" -type "string" "/textures/asset/displacement.<UDIM>.exr";
createNode file -n "roughness_tex";
	rename -uid "E5F6A7B8-C9D0-1234-EFAB-345678901234";
	setAttr ".fileTextureName" -type "string" "/textures/asset/roughness.tx";
createNode place2dTexture -n "place2d_diffuse";
createNode place2dTexture -n "place2d_disp";
createNode place2dTexture -n "place2d_rough";
// End of scene_with_textures.ma
