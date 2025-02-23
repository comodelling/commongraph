# Configuration

Here we go through the different configuration options offered when deploying an instance of ObjectiveNet.
For user-related settings, see the [user's views](view_user.md) .

## Graph database


By default, the app can run simply using a postgresql relational database.
However, you can also enable a janusgraph graph database on top of the relational database to speed up graph-related queries.
To do so, just set `ENABLE_GRAPH_DB` to `true` in `backend/.env` configuration file.


!!! note

    Switching between graph database enabled or not might lead to inconsistencies.


## Random quotes

For randomly selecting and displaying quotes on your instance's main page, you can specify the path to JSON file of quotes in `backend/.env`.
For instance: ```QUOTES_FILE=path_to_your_quotes_file.json```.
The JSON file should be formatted with a quote, author, and optional "where" field, e.g.:
```json
{
    "quote": "Being concerned with the way our actions and beliefs now, today, will shape the future, tomorrow, the next generations.",
    "author": "Adrienne Maree Brown",
    "where": "Emergent Strategy, p16",
}
```
