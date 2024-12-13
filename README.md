# ObjectiveNet

This project uses:
- fastAPI framework and a janusgraph graph database on the backend,
- [Vue](https://vuejs.org/) 3, [Vite](https://vite.dev/), and [Vue Flow](https://vueflow.dev/) on the fronend.

It is dockerised, so you'll need to have Docker installed to run it.

## Usage

To start the project, run: ```docker compose up```

Then you should be able to access: http://localhost:8000/network/summary to query the number of nodes and edges in the (local) database.


## Contributing


### Dev setup

To generate new .txt requirements files from .in, you'll need pip-tools: ```pip install pip-tools```<br>
Then, you can run: ```pip-compile requirements.in``` or ```pip-compile requirements-dev.in``` whenever you update these `.in` files.

Run `pre-commit install` to set up the git hook scripts. It'll check that some formatting and unit tests are met before any commit.

## License

This project is licensed under the GNU Affero General Public License - see the [COPYING](COPYING) file for details.

## Contact Information

For any inquiries, please contact [Mario](mario.morvan@ucl.ac.uk).
