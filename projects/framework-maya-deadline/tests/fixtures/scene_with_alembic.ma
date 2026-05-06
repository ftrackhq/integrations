//Maya ASCII 2025 scene
//Name: scene_with_alembic.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "AbcImport" "1.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "cache_GRP";
createNode AlembicNode -n "abc_cache1";
	setAttr ".abc_File" -type "string" "/cache/anim/character_v001.abc";
	setAttr ".startFrame" 1001;
	setAttr ".endFrame" 1100;
// End of scene_with_alembic.ma
