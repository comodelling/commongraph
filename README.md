# ObjectiveNet

ObjectiveNet is a free software for modelling possible changes as nodes in a causal network.

## Usage

To start ObjectiveNet:

- [install Docker engine](https://www.docker.com/get-started/) if not already on your machine,
- clone the repo, e.g. with ```git clone https://github.com/comodelling/objectivenet.git``` from a terminal,
- run ```bash start_docker.sh``` from the cloned `objectivenet/` directory,
- wait for it to start...and that's it! you can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.


## Development

This project uses:
- [FastAPI](https://fastapi.tiangolo.com/) framework, [JanusGraph](https://janusgraph.org/) graph database and [PostgreSQL](https://www.postgresql.org/) relational database on the backend,
- [Vue.js](https://vuejs.org/), [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the frontend.

### Backend API

ObjectiveNet's graph database can also be queried directly using its backend API framework.
You can find its API schema at: [http://localhost:8000/docs](http://localhost:8000/docs) (generated automatically using Swagger).


### Database configuration

By default, the app can run simply using a postgresql relational database.
However, you can also enable a janusgraph graph database on top of the relational database to speed up some queries.
To do so, just set `ENABLE_GRAPH_DB` to `true` in `backend/.env` configuration file.

*Note*: switching between graph database enabled or not might lead to inconsistencies.

### Contributing

Looking to file a bug report or a feature request? [https://github.com/comodelling/objectivenet/issues](https://github.com/comodelling/objectivenet/)

You can also contribute to ObjectiveNet by:
- experimenting with the software and directly [sending feedback via email](mailto:mario.morvan@ucl.ac.uk),
- creating feature/ or fix/ branches and opening [pull requests](https://github.com/comodelling/objectivenet/pulls).


### Dev tools

It is recommended to install dev requirements within a virtual environment when contributing to the code: `pip install -r requirements-dev.txt` (this includes the main requirements).

Run `pre-commit install` to set up the git hook scripts. It'll perform some formatting, linting, unit tests, and version sync before any commit.

To generate new *.txt* requirements files after updating *.in* requirements files, you can run: ```pip-compile backend/requirements.in``` or ```pip-compile backend/requirements-dev.in```.


### Database export

In addition to JSON exports of networks through the graphical UI or backend API, one can export the whole data volume for the janusgraph container.
Simply replace /path/to/backup with the absolute path to your backup directory in the commands below.

Create backup:
```docker run --rm -v objectivenet_janusgraph-mount-data:/volume -v /path/to/backup:/backup alpine sh -c "cd /volume && tar czf /backup/janusgraph-mount-data-backup.tar.gz ."```

Restore backup (restart required afterwards):
```docker run --rm -v objectivenet_janusgraph-mount-data:/volume -v /path/to/backup:/backup alpine   sh -c "cd /volume && tar xzf /backup/janusgraph-mount-data-backup.tar.gz"```


## License

This project is licensed under the GNU Affero General Public License - see the [COPYING](COPYING) file for details.

© 2024 Mario Morvan
