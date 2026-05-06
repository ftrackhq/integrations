//Maya ASCII 2025 scene
//Name: scene_with_gpu_cache.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
requires "gpuCache" "1.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode transform -n "gpu_cache_GRP";
createNode gpuCache -n "building_cache";
	setAttr ".cacheFileName" -type "string" "/cache/gpu/building_v002.abc";
	setAttr ".cacheGeomPath" -type "string" "|building_GRP|building_GEO";
// End of scene_with_gpu_cache.ma
