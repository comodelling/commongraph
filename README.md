# ObjectiveNet

## Installation


## Usage

```fastapi dev main.py```

### Database setup

run docker container for local janusgraph server:
```docker run -it -p 8182:8182 \
  -v full_path_to_janusgraph_config_path/janusgraph-server.yaml:/etc/opt/janusgraph/janusgraph-server.yaml \
  -v full_path_to_janusgraph_config_path/main.properties:/etc/opt/janusgraph/main.properties \
  -v full_path_to_janusgraph_config_path/test.properties:/etc/opt/janusgraph/test.properties \
  -v full_path_to_janusgraph_config_path/traversal-sources.groovy:/etc/opt/janusgraph/scripts/traversal-sources.groovy \
  janusgraph/janusgraph
```


docker run -it -p 8182:8182 -v $full_path_to_janusgraph_config_path/janusgraph-server.yaml:/etc/opt/janusgraph/janusgraph-server.yaml:ro  -v $full_path_to_janusgraph_config_path/test.properties:/etc/opt/janusgraph/test.properties:ro -v $full_path_to_janusgraph_config_path/main.properties:/etc/opt/janusgraph/main.properties:ro -v $full_path_to_janusgraph_config_path/empty-sample.groovy:/opt/janusgraph/scripts/empty-sample.groovy:ro janusgraph/janusgraph

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

For any inquiries, please contact [Mario](mario.morvan@ucl.ac.uk).
