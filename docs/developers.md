# Developers

## Database configuration

You can choose between different types of databases to store the underlying graph by modifying the value of `DB_TYPE` inside `backend/.env` configuration file.
Currently supported database types are: `janusgraph`, `sqlite`.

!!! note

    there is no synchronisation between those different databases, and switching between them will not import the content of the other. For this, you will need to export and import the content using the `network` API.


## Backend API

ObjectiveNet's graph database can also be queried directly using its backend API framework.
You can find its API schema at: [http://localhost:8000/docs](http://localhost:8000/docs) (generated automatically using Swagger).


## Development

This project uses:
- [FastAPI](https://fastapi.tiangolo.com/) framework and a [JanusGraph](https://janusgraph.org/) graph database on the backend (or relational alternatives such as [SQlite](https://www.sqlite.org)),
- [Vue.js](https://vuejs.org/), [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the frontend.


## Contributing

Looking to file a bug report or a feature request? https://github.com/comodelling/objectivenet/issues

You can also contribute to ObjectiveNet by:

- experimenting with the software and directly [sending feedback via email](mailto:mario.morvan@ucl.ac.uk),
- creating **feature/** or **fix/**  branches and opening [pull requests](https://github.com/comodelling/objectivenet/pulls).
