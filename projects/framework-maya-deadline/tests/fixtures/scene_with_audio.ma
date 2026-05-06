//Maya ASCII 2025 scene
//Name: scene_with_audio.ma
//Last modified: Thu, May 01, 2025 12:00:00 PM
requires maya "2025";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2025";
fileInfo "version" "2025";
createNode audio -n "audioTrack1";
	setAttr ".filename" -type "string" "/audio/dialogue_take3.wav";
	setAttr ".offset" 0;
	setAttr ".sourceStart" 0;
	setAttr ".sourceEnd" 48000;
// End of scene_with_audio.ma
