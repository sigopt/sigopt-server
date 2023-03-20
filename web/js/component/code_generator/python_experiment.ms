from sigopt import Connection

conn = Connection(client_token="{{& apiToken}}")
{{#apiUrl}}
conn.set_api_url("{{apiUrl}}")
{{/apiUrl}}
