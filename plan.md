**Wishnet Development Plan**

This document outlines a dynamic plan for developing a piece of software currently known as *Wishnet*. Broadly, the programme enables creating, editing, and sharing *entities* related together through a *causal network*. These entities could represent various things, but the primary purpose is currently to use it for sharing *wishes*, *proposals*, and *objectives* at different scales, allowing individuals and non-profit organisations to collaborate towards their common goals.

**Features**

**Basic/Core Features**
- Some standard types of entities are available: e.g., wishes, proposals, objectives, changes-in-the-world, each with their respective attributes.
- Two main types of links are available: requirements and implications. Their core attributes are conditional probabilities (p(requirement|entity) and p(implication|entity)) with causal interpretation. They can also include a list of sources/references.
- Initially, all elements are public, and anyone can add or edit any element in the network.

**Important Features**
- User roles are introduced later, including basic and admin, with default permissions that can be customised.
- Only logged-in users can add, edit, or delete entities and links.
- Admins can alter the configuration of Wishnet's implementation.
- Entities and links can be "gradable" (on a fixed qualitative scale) or "quantifiable" (on a fixed quantitative scale). If activated for a given element, any user can change the element's grade. Each type of element has a fixed associated scale, but this can differ for each type of element.

**Extended Features**
- Database user interface, useful especially for searching through proposals using semantic search, tags, attributes, etc. Can be connected to the graph user interface.
- Graph user interface:
  - An accessible and intuitive interface allowing users to edit entities' attributes and relate them to other entities via two types of links: requirements and implications.
  - An interface to visualise existing networks in exploration mode, linked to the database.
  - An interface to visualise the network in editing mode.
- Flexible/configurable entities: their names, the number of them, and their attributes. In a given instance of the software, one can specify what entities are allowed.
- More fine-grained rights for users, with rights granted individually by admins and/or more levels of rights.
- Elements can be public or private. If private, they can be shared with a group of users.
- Groups of users not only facilitate sharing private elements but can also own an entity. A user within a group can decide for the group to own a newly created element, or to transfer it later.
- Different methods can be configured to grade an element, going beyond simple editing. For instance, the grade may be determined as the median grade among all users who've graded it.

**Future Features**
- Some user data is collected privately, with high privacy standards and policies.
- Entities' scopes can be directly linked with some user characteristics such as residence location (which can be broad), age, etc., to determine who can grade/what importance to give to the weight for a given element.

**Technology**

**Back-end**

**Database**
- As we're building an arbitrarily large graph of entities with connections between them, it makes sense to use a graph database.
- We're currently planning to use JanusGraph for its scalability, open-source nature, and support for multiple storage backends.
- JanusGraph is based on Apache TinkerPop, providing a standardised API for graph databases.
- For decentralised storage, consider integrating IPFS (InterPlanetary File System) for data replication and synchronisation.

**Graph Query Language**
- Gremlin if using Apache TinkerPop (so compatible with JanuGraph and also python through `gremlinpython` library)

**Back-end App Language**
- Stick with Python for its ease of use, extensive libraries, and good integration with Neo4j via the Neo4j Python driver.
- Alternatively, consider Java for its robustness and performance, especially for large-scale applications.

**Front-end**
- **UI Framework**: Use React.js for its flexibility, component-based architecture, and extensive community support. Alternatively, consider Vue.js for its simplicity and ease of integration with other libraries.

**Wishnet Accessible Language**
- Create a simpler language for editing entities, (inspired by MediaWiki, which has simplified HTML and specific syntax for links, and powers Wikipeia). 
- The simpler and more effective, the better.


**Development Strategy**

- Aim to prototype the idea and keep refining/adapting this current plan.
  - Keep things light, modular, and flexible, so as to be able to adapt things later.
- Build the software incrementally, by prototyping things quickly while thinking more carefully about decisions that will be harder to reverse later.
- Aim to be able to test and experiment with the software throughout the development. Facilitating testing and experiments will therefore be useful.
- Aim to open-source the software later on, once important questions have been decided: licensing, usability risks, governance (me or an organisation), etc.

**Security Considerations**
- Implement role-based access control to ensure data integrity.
- Use encryption and secure authentication methods to protect user data.
- Establish clear privacy policies for user data collection.

**Testing Strategy**
- Employ unit testing, integration testing, and user acceptance testing.
- Incorporate user feedback into the development process through beta testing.
- Utilise automated testing tools to ensure consistent quality.

**Documentation**
- Provide comprehensive documentation for developers and users to ensure ease of use and development.
- Include API documentation for external developers.
- Create user guides and tutorials for end-users.
