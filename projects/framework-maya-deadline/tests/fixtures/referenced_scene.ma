//Maya ASCII 2025 scene
//Name: referenced_scene.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "character_GRP";
createNode mesh -n "bodyShape" -p "character_GRP";
createNode shadingEngine -n "body_SG";
createNode lambert -n "body_MAT";
createNode file -n "diffuse_tex";
	rename -uid "A1B2C3D4-E5F6-7890-ABCD-EF1234567890";
	setAttr ".fileTextureName" -type "string" "/textures/char/diffuse.exr";
createNode file -n "normal_tex";
	rename -uid "B2C3D4E5-F6A7-8901-BCDE-F12345678901";
	setAttr ".fileTextureName" -type "string" "/textures/char/normal.exr";
createNode place2dTexture -n "place2d_diffuse";
createNode place2dTexture -n "place2d_normal";
// End of referenced_scene.ma
