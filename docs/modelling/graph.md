# Graph of Change

In ObjectiveNet, possible changes are modelled as **nodes** in a **graph**, which may be connected together by **edges**.

## Nodes

Nodes are the main entities in a graph. They are conceived as *possible changes* for the purpose of ObjectiveNet.
One can create or edit a node via the node info pane.

Every node must have the following attributes:

- **type**, among **objective** (i.e. goal, purpose), **action**, **project**, and **potentiality** (i.e. possibility, externality)
- **title**, to contain a short, one-line summary of the possible change
- **scope**, which indicates where/to whom the change should apply

Additionally, the following attributes can be added to any node:

- **status**, among *live*, *draft*, *completed*, *legacy*,
- a list of **tags**,
- a list of **references**,
- a longer **description**,
- a measure of the [**support level**](demos.md#support-ratings)

## Edges

Edges connect two nodes together, representing a *causal relation* in a loose way, in which one node would be *enabling/causing/implying* another.

Each edge may have the following attributes associated to it:

- a list of **references**,
- a longer **description**,
- a measure **causal strength**, encompassing both aspects of necessity and sufficiency.
