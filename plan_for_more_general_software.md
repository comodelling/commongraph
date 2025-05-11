



Admin can define a metamodel:
- which chiefly defines the possible:
    - types of nodes. Each type has got a name (variable and display), but also several attributes (with a variable name, name and a data type like string, number, ...), and polls (with a variable name, a question, a rule for voting...)
    - edges between the different types of nodes
- based off an existing template or from scratch. Same for the types of nodes, relations, attributes and polls: there are template ones but it will be possible to create some new ones.
- a style may be associated or changed with each entity type (nodes, edges, attributes...)
- at first maybe just directly from a config file but later will be possible through a graphical interface.


Below some examples of possible simple formats for defining a metamodel (may require more details, for types, style etc... but it should give an idea)

example 1:
- types of nodes: 
    - source
        - title: ...
        - source_type: (book, speech, article...)
        - source_url
        - *source specific fields...*
    - quote
        - title
        - language
    - author
        - name
- types of edges: 
    - author -produced-> source
    - source -contains-> quote
        - page 


example 2:
- types of nodes: 
    - change/project/action
        - title
        - description
        - references (list)
        - users rating (e.g., Likert Scale)
    - question
        - title
        - description
        - references (list)
        - user ratings
    - objective
        - title
        - description
        - references (list)
        - user ratings
- types of edges: 
    - change -implies-> change
        - necessity (0-1)
        - sufficiency (0-1)
        - causal strength (mix of necessity and sufficiency)
        - user ratings
    - question -motivates-> change
    - objective -motivates-> change


