# ObjectiveNet

*ObjectiveNet* is a free software for modelling possible changes as nodes in a causal graph.

See its [documentation](https://comodelling.github.io/objectivenet/) for more tips and information.

## Quick Start

To start ObjectiveNet:

- [Install Docker engine](https://www.docker.com/get-started/) if not already on your machine.
- Clone the repo, e.g. with ```git clone https://github.com/comodelling/objectivenet.git```.
- Run ```./start_docker.sh up --build -d``` from the cloned `objectivenet/` directory.
- Wait for it to start... and that's it! You can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.


## Contributing

Looking to file a bug report or a feature request? [https://github.com/comodelling/objectivenet/issues](https://github.com/comodelling/objectivenet/)

You can also contribute to ObjectiveNet by:
- experimenting with the software and directly [sending feedback via email](mailto:mario.morvan@ucl.ac.uk),
- creating feature/ or fix/ branches and opening [pull requests](https://github.com/comodelling/objectivenet/pulls).


## For Developers

This project uses:
- [FastAPI](https://fastapi.tiangolo.com/) framework, a [PostgreSQL](https://www.postgresql.org/) relational database and a [JanusGraph](https://janusgraph.org/) graph database on the backend,
- [Vue.js](https://vuejs.org/), [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the frontend.

### Backend API

ObjectiveNet's graph database can also be queried directly using its backend API framework.
You can find its API schema at: [http://localhost:8000/docs](http://localhost:8000/docs) (generated automatically using Swagger).

### Dev tools

It is recommended to install dev requirements within a virtual environment when contributing to the code: `pip install -r requirements.txt -r requirements-dev.txt` (this includes the main requirements).

Run `pre-commit install` to set up the git hook scripts. It'll perform some formatting, linting, unit tests, and version sync before any commit.

To generate new *.txt* requirements files after updating *.in* requirements files, you can run: ```pip-compile backend/requirements.in``` or ```pip-compile backend/requirements-dev.in```.


## License

This project is licensed under the GNU Affero General Public License - see the [COPYING](COPYING) file for details.

© 2025 Mario Morvan
