# Welcome to ObjectiveNet Documentation

*ObjectiveNet* is a free software for modelling possible changes as nodes in a causal network.<br>
It is in development, and its current state may differ from this documentation.

## Getting started

To start ObjectiveNet:

- [install Docker engine](https://www.docker.com/get-started/) if not already on your machine,
- clone the repo, e.g. with ```git clone https://github.com/planningcommons/objectivenet.git```,
- run ```bash start_docker.sh``` from the cloned `objectivenet/` directory,
- wait for it to start...and that's it! You can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.

You will be able to create possible changes, relate them together, visualise them, and search for them through the web interface.
Changes are interconnected as part of a [causal graph](graph.md), and their [support level](democracy.md) may be measured.
