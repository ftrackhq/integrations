# How to extend the opener:
- Add new plugin in the plugins list of the photoshop-document-opener.json tool-config
Example:
```json
	"plugins": [
	    {
	      "plugin_type": "fetch",
	      "plugin_title": "Fetch from ftrack",
	      "plugin_name": "ftrack_assets_fetcher",
	      "widget_name": "asset_version_browser_selector"
	    },
	    {
	      "plugin_type": "fetch",
	      "plugin_title": "Fetch from local",
	      "plugin_name": "local_files_fetcher",
	      "widget_name": "file_browser_collector"
	    }
	  ]
```

- Create the "local_files_fetcher" plugin. (You can youse the ftrack_assets_fetcher as template)

- Create the "file_browser_collector" widget. (You can use asset_version_browser_selector as template)
	- Make sure to have the fetch function and the selected_assets property. (The opener_publisher_tab_dialog makes use of this two)

- Extend the path_collector plugin to deal with the selected_assets returned from your fetcher plugin.
	- If your fetcher plugin returns filepaths, you could add a `return options.get('selected_assets')` if you don't have to process them.

# How to extend the publisher with the version up button:
- Fill out the photoshop_local_version_up_document run method.
- Note: In case you want to change the name of the plugin, make sure the plugin_name is updated in the _on_ui_version_up_button_clicked_callback method of the opener_publisher_tab_widget file.
- Note: If you want to get the result of the version up plugin in the dialog, please re-implement the method _on_client_notify_ui_run_plugin_result_callback in your dialog.
