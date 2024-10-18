This document outlines a dynamic plan for developing a piece of software currently called *Wishnet*.
Very broadly, the program enables creating, editing, and sharing *entities* related together through a *causal network*.
These entities could be different things, but the primary purpose is currently to use it for sharing *wishes*, *proposals*, and *objectives* at different scales, allowing individuals and non-profit organizations to work together towards their common goals.

# Features

## Basic/Core Features
- Some standard types of entities are available: e.g., wishes, proposals, objectives, changes-in-the-world, with their respective attributes.
- Two main types of links are available: requirements and implications. Their core attributes are conditional probabilities (p(requirement|entity) and p(implication|entity)) with causal interpretation. They can also include a list of sources/references.
- All elements are 'public' 
- there is no user, or all users can add or edit any element in the network.

## Important Features
- User roles include basic and admin, with default permissions that can be customized.
- only logged-in users can add, edit, or delete entities and links.
- admins can change the configuration of Wishnet implementation.
- entities and links can be "gradable" (on a fixed qualitative scale) or "quantifiable" (on a fixed quantitative scale). That is to say, if activated for a given element, any user can change the element's grade. Each type of element (a 'wish', a 'proposal', a 'need', 'requirement'...) has a fixed associated scale to it, but that can be different for each type of element.  

## Extended Features
- Database user interface, useful especially when searching through proposals using semantic search, tags, attributes etc. Can be connected to graph user interface.
- Graph user interface:
  - An accessible and intuitive interface allows users to edit entities' attributes and relate them to other entities via two types of links: requirements and implications.
  - An interface to visualize existing networks in exploration mode, linked to the database.
  - An interface to visualize the network in editing mode.
- Flexible/configurable entities: their names, the number of them, and their attributes. In a given instance of the software, one can specify what entities are allowed.
- More fine-grained rights for users, with either rights granted individually by admins and/or more levels of rights.
- elements can be public or private. If they are private, they can be shared with a group of users.
- groups of users not only facilitate sharing private elements but can also own an entity. A user part of a group can indeed decide for this group to own a newly created element, or to transfer it later. 
- different methods can be configured to grade an element, going beyond simple editing. For instance, the grade may be determined as the median grade among all users who've graded it. 

## Future Features
- Some user data is collected privately, with high privacy standard and policies
- Entities scopes can be directly linked with some user characteristics such as residence location (can be broad), age, etc...to determine who can grade/what importance give to the weight for a given element.


# Tech

## Back-end

### Database
Since we're building an arbitrarily large graph of entities with connections between them, it makes sense to use a graph database.
At the moment, we're planning on using a Neo4j database.
Possibility for decentralised database or necessarily centralised? I guess we're just talking of the public side of Wishnet here, of course.

### Graph Query Language
CYPHER for a Neo4j database?
I guess here it's going to be hidden from the user.

### Back-end App Language
I'm comfortable with Python and it should have integrations with many other useful libraries, languages?
For instance, with Neo4j?

## Front-end
- **UI Framework**: Consider using React.js or Vue.js for a dynamic and responsive user interface.

## Wishnet Accessible Language
How to make something even simpler to edit than CYPHER and fitted for Wishnet's purpose?
The example I have in mind is MediaWiki, which has simplified HTML and made particular choices for links syntax, etc., fitted for Wikipedia.
The simplest and most effective, the better.

# Development Strategy

- Aiming to prototype the idea and keep refining/adapting this current plan.
  - Keeping things light, modular, and flexible, so as to be able to adapt things later.
- Building software incrementally, by prototyping things fast while thinking more carefully of decisions that will be harder to reverse later.
- Aiming at being able to test and experiment with the software throughout the development. Facilitating testing and experiments will therefore be useful.
- Aiming at open-sourcing the software only later on when some important questions have been decided: licensing, usability risks, governance (me or an organization), etc.

# Security Considerations
- Use encryption and secure authentication methods to protect user data.

# Testing Strategy
- Employ unit testing, integration testing, and user acceptance testing.
- Incorporate user feedback into the development process through beta testing.

# Documentation
- Provide comprehensive documentation for developers and users to ensure ease of use and development.