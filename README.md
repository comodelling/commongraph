# ObjectiveNet

## Installation


## Usage

```fastapi dev main.py```

### Database setup

run docker container for local janusgraph server:
```docker run -it -p 8182:8182 janusgraph/janusgraph```

## Contributing

### Dev setup

to generate .txt requirements files from .in, install pip-tools:
```pip install pip-tools```
then you can run:
```pip-compile requirements.in```
and
```pip-compile requirements-dev.in```
whenever you update these `.in` files.

### Guidelines

run `pre-commit install` to set up the git hook scripts, then `pre-commit run --all-files` before committing.

## License

This project is licensed under the GNU Affero General Public License - see the [COPYING](COPYING) file for details.

## Contact Information

For any inquiries, please contact [Mario M.](mario.morvan@ucl.ac.uk).
