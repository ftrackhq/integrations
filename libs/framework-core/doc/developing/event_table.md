# Integrations Framework Events Table
| Host                                        | Event                        | Client                                           | Event Description                                                                                                                                                               |
|---------------------------------------------|------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Subscribe(host)                             | DISCOVER_HOST_TOPIC          | Publish(client)                                  | The client publish an event and waits for a reply in host, can't do it the other way around because host is initialized first and we can't have a list of all published events. |
| Subscribe(host)                             | HOST_RUN_TOOL_CONFIG_TOPIC   | Publish(Client)                                  | Client emits this event to tell the host to run the provided tool config, on behalf of the client.                                                                              |
| Subscribe(host)                             | HOST_RUN_UI_HOOK_TOPIC       | Publish(Client)                                  | Client emits this event to tell the host to run the ui_hook method of the provided plugin config, on behalf of the client.                                                      |
| Publish(host)                               | HOST_CONTEXT_CHANGED_TOPIC   | Subscribe(Host connection)<br/>Subscribe(client) | Event emitted every time host changes the context                                                                                                                               |
| Subscribe(host)                             | CLIENT_CONTEXT_CHANGED_TOPIC | Publish(Host connection)                         | Context has been changed in the client side, needs to communicate this to the host.                                                                                             |
| Publish(host)                               | HOST_LOG_ITEM_ADDED_TOPIC    | Subscribe(client)                                | New log item has been added                                                                                                                                                     |
| Publish(host)                               | HOST_UI_HOOK_RESULT_TOPIC    | Subscribe(client)                                | New UI_HOOK result received from host to client.                                                                                                                                |

| UI                              | Event                                | Client          | Event Description                                                                      |
|---------------------------------|--------------------------------------|-----------------|----------------------------------------------------------------------------------------|
| Subscribe(BaseWidget)           | CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC  | Publish(client) | Context has been changed, this is just a signal, no data is emitted, needs client_id.  |
| Subscribe(BaseWidget)           | CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC | Publish(client) | Hosts has been discovered, this is just a signal, no data is emitted, needs client_id. |
| Subscribe(BaseWidget)           | CLIENT_SIGNAL_HOST_CHANGED_TOPIC     | Publish(client) | Host has been changed, this is just a signal, no data is emitted, needs client_id.     |
| Subscribe(BaseWidget)           | CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC   | Publish(client) | LOG item added in the host, and client send the log item to the UI.                    |
| Subscribe(BaseWidget)           | CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC   | Publish(client) | ui_hook method result received in the host, and client forward the result to the UI.   |

| Remote(JS) | Event                                 | RemoteConnection/Python | Event Description                                                                                                  |
|------------|---------------------------------------|-------------------------|--------------------------------------------------------------------------------------------------------------------|
| Publish    | DISCOVER_REMOTE_INTEGRATION_TOPIC     | Subscribe               | Remote integration<>Python communication; Discovery and alive check                                                |
| Subscribe  | DISCOVER_REMOTE_INTEGRATION_TOPIC     | Publish                 | Remote integration<>Python communication; Discovery and alive check                                                |
| Subscribe  | REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC | Publish                 | Remote integration<>Python communication; Provide context data to JS integration                                   |
| Publish    | REMOTE_INTEGRATION_RUN_DIALOG_TOPIC   | Subscribe               | Remote integration<>Python communication; Launch tool                                                              |
| Subscribe  | REMOTE_INTEGRATION_RPC                | Publish                 | Remote integration<>Python communication; Remote integration<>Python communication; Run JS function with arguments |




