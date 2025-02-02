# ObjectiveNet

*ObjectiveNet* is a free software for modelling possible changes as nodes in a causal graph.
 It aims to foster open, inclusive, collaborative and objective-based decision-making processes.<br>


!!! warning

    ObjectiveNet is in alpha development, and its current state may differ from this documentation.


## Getting Started

To start ObjectiveNet:

- [install Docker engine](https://www.docker.com/get-started/) if not already on your machine,
- clone the repo, e.g. with ```git clone https://github.com/comodelling/objectivenet.git```,
- run ```bash start_docker.sh``` from the cloned `objectivenet/` directory,
- wait for it to start...and that's it! You can access it at [http://localhost:5173/](http://localhost:5173/) from a browser.

You will be able to create possible changes, relate them together, visualise them, and search for them through the web interface.
Changes are interconnected as part of a [causal graph](graph.md), and their [support level](democracy.md) may be measured through support ratings.



## Logging in

Users have the ability sign up (`/signup`) and log in (`/login`) using the log in interface, and update their preferences in their user settings (`/settings`).
A security question and answer can be set to be able to reset one's password.

By default, non-logged in users can also access and edit the graph.
However, logging in will unlock a few rights to users such as rating nodes, saving pages.
