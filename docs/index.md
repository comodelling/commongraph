# ObjectiveNet

*ObjectiveNet* is a free software for modelling possible changes as nodes in a causal graph.
 It aims to foster open, inclusive, collaborative and objective-based decision-making processes.<br>


!!! warning

    Please note that ObjectiveNet is currently in its alpha stage. This phase involves may involve frequent changes, including breaking ones. We recommend using it primarily for testing and [feedback](mailto:mario.morvan@ucl.ac.uk).


## Getting Started

To start ObjectiveNet:

- [Install Docker engine](https://www.docker.com/get-started/) if not already on your machine.
- Clone the repo, e.g. with ```git clone https://github.com/comodelling/objectivenet.git```.
- Run ```bash start_docker.sh``` from the cloned `objectivenet/` directory.
- Wait for it to start... and that's it! You can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.

You will be able to create possible changes, relate them together, visualise them, and search for them through the web interface.
Changes are interconnected as part of a [causal graph](modelling/graph.md), and their [support level](modelling/support.md) may be measured through support ratings.
