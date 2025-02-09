# Developers

## Database configuration


By default, the app can run simply using a postgresql relational database.
However, you can also enable a janusgraph graph database on top of the relational database to speed up some queries.
To do so, just set `ENABLE_GRAPH_DB` to `true` in `backend/.env` configuration file.


!!! note

    switching between graph database enabled or not might lead to inconsistencies.


## Backend API

ObjectiveNet's graph database can also be queried directly using its backend API framework.
You can find its API schema at: [http://localhost:8000/docs](http://localhost:8000/docs) (generated automatically using Swagger).


## Development

This project uses:
- [FastAPI](https://fastapi.tiangolo.com/) framework, [JanusGraph](https://janusgraph.org/) graph and  [PostgreSQL](https://www.postgresql.org/) relational databases on the backend,
- [Vue.js](https://vuejs.org/), [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the frontend.


## Contributing

Looking to file a bug report or a feature request? [https://github.com/comodelling/objectivenet/issues](https://github.com/comodelling/objectivenet/)

You can also contribute to ObjectiveNet by:

- experimenting with the software and directly [sending feedback via email](mailto:mario.morvan@ucl.ac.uk),
- creating **feature/** or **fix/**  branches and opening [pull requests](https://github.com/comodelling/objectivenet/pulls).
