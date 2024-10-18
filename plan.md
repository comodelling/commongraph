This document outlines a dynamic plan for developing a piece of software currently called *Wishnet*. 
Very broadly, the program enables creating, editing and sharing *entities* related together through a *causal network*. 
These entities could be different things, but the primary purpose is currently to use it for sharing *wishes*, *proposals* and *objectives* at different scales, allowing individuals and non-profit organisations to work together towards their common goals.


# Features

## basic/core features
- some standard types of entities are available: e.g. wishes, proposals, objectives, changes-in-the-world, ... with their respective attributes
- two main types of links are available: requirements and implications. Their core attributes are conditional probabilities (p(requirement|entity) and p(implication|entity)) with causal interpretation. They can also a list of sources/references.
- anyone can add or edit any element in the network


## Important features
- there are different users, only logged-in users can 


## Extended features
- database user interface
- grah user interface:
    - an accessible and intuitive interface allows users to edit entities' attributes, and relate them to other entities via two types of links: requirements and implications 
    - an interface to visualise existing networks exploration mode, linked to database)
    - an interface to visualise network in editing mode

- flexible / configurable entities: their names, the number of them, and their attributes. In a given instance of the software, one can specify what entities are allowed. 
- each type of user contribution has an associate right and users can be given more or less rights on a right-per-right level. There could be default profiles (e.g. basic and admin) that simplify this management. 

# Tech

## Back-end

### database
Since we're building an arbitrarily large graph of entities with connections between them, it makes sense to use a graph database. 
At the moement we're planning on using a Neo4j database.

### Graph Query Language
CYPHER for a Neo4j database?
I guess here it's going to be hidden from user so 

### Back-end app language
I'm comfortable with Python and it should have integrations with many other useful libraries, languages? 
For instance, with Neo4j?

## Front-end 
## Wishnet accessible Language 
how to make something even simpler to edit than CYPHER and fitted for Wishnet's purpose? 
The example I have in mind is MediaWiki that has simplified HTML and made particular choices for links syntax etc... fitted for Wikipedia.
The simplest and most effective, the better.

## UI framework 
This is where I am clueless at the moment, though the UI is also something that is potentially less urgent than the back-end. 



# Development strategy

* aiming to prototype the idea and keep refining/adapting this current plan
    * keeping things light, modular, and flexible, so as to be able to adapt things later
* building software incrementally, by prototyping things fast while thinking more carefully of decisions that will be harder to reverse later
* aiming at being able to test and experiment with the software throughout the development. Facilitating testing and experiments will therefore be useful. 
* aiming at open sourcing the software only later on when some important questions have been decided: licensing, usability risks, governance (me or an organisation), etc...
