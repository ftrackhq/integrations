# ftrack QT library release Notes

## v2.1.0
2024-04-02

* [fixed] asset_list widget clear list before setting new assets.
* [changed] Widget file names align within the same folder.
* [changed] widgets/frame folder renamed to asset.
* [changed] Moved OpenAssetSelector logic to AssetSelectorBase.
* [fixed] Fixed bug in asset_selector, if no assets on startup - properly emit asset name changed signal.
* [fixed] Disabled auto scrolling on asset list. Always select the first item on activation.
* [new] selectors/asset_selector; Change behaviour of new asset button and the name input field, list is greyed out during creation. Asset name input is hidden when an existing asset is selected. 

## v2.0.1
2024-03-08

* [fix] asset_selector; Fix resize bug.

## v2.0.0
2024-02-12

*  [new] Initial release.
