# ObjectiveNet

ObjectiveNet is an open source software to help people build causal networks of objectives, actions, and potentialities.

## Usage

To start ObjectiveNet:

- [install Docker](https://www.docker.com/get-started/) if not already on your machine,
- clone the repo, e.g. with ```git clone https://github.com/planningcommons/objectivenet.git``` from a terminal,
- run ```bash start.sh``` from the cloned *objectivenet/* directory,
- wait for it to start...and that's it! you can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.


### Backend API

ObjectiveNet's graph database can also be queried directly using its backend API framework.
You can find its API schema at: http://localhost:8000/docs (generated automatically using Swagger).


## Development

This project uses:
- [FastAPI](https://fastapi.tiangolo.com/) framework and a [JanusGraph](https://janusgraph.org/) graph database on the backend,
- [Vue.js](https://vuejs.org/), [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the frontend.


### Contributing

Looking to file a bug report or a feature request? https://github.com/planningcommons/objectivenet/issues

You can also contribute to ObjectiveNet by:
- experimenting with the software and directly [sending feedback via email](mario.morvan@ucl.ac.uk),
- creating feature/ or fix/ branches and opening [pull requests](https://github.com/planningcommons/objectivenet/pulls).


### Dev tools

It is recommended to install dev requirements within a virtual environment when contributing to the code: `pip install -r requirements-dev.txt` (this includes the main requirements).

Run `pre-commit install` to set up the git hook scripts. It'll perform some formatting, linting and unit tests before any commit.

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
