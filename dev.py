from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
from gremlin_python.process.anonymous_traversal import traversal
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g', message_serializer=GraphSONSerializersV3d0())
# The connection should be closed on shut down to close open connections with connection.close()
g = traversal().withRemote(connection)
# Reuse 'g' across the application


# Check if any vertices exist
vertex_count = g.V().count().next()

if vertex_count:
    g.V().drop().iterate()

# Create vertices
v1 = g.addV('wish').property('id', 'wish1').property('name', 'Wish 1').next()
v2 = g.addV('wish').property('id', 'wish2').property('name', 'Wish 2').next()
v3 = g.addV('wish').property('id', 'wish3').property('name', 'Wish 3').next()
v4 = g.addV('wish').property('id', 'wish4').property('name', 'Wish 4').next()
v5 = g.addV('wish').property('id', 'wish5').property('name', 'Wish 5').next()

# Create edges
g.V().has('id', 'wish1').addE('requirement').to(__.V().has('id', 'wish2')).next()
g.V().has('id', 'wish1').addE('requirement').to(v3).next()
g.V().has('id', 'wish1').addE('implication').to(__.V().has('id', 'wish4')).next()
g.V().has('id', 'wish1').addE('implication').to(__.V().has('id', 'wish5')).next()

# Summary
print(f'Total vertices in the graph: {g.V().count().next()}')
print(f'Total edges in the graph: {g.E().count().next()}')

# Visualization
# Create a NetworkX graph
G = nx.DiGraph()

# Add nodes
vertices = g.V().toList()
print(vertices)
for vertex in vertices:
    #name = vertex.properties('name').value()
    print('(gremlin) vertex id', vertex.id)
    print('vertex label', vertex.label)
    print('vertex properties', vertex.properties)
    d = {p.key: p.value for p in vertex.properties}
    #print(dir(vertex.properties))
    #vertex_name = vertex.properties('name').next()
    G.add_node(vertex.id, type=vertex.label, name=d['name'])

# Add edges
edges = g.E().toList()
for edge in edges:
    if edge.label == 'implication':
        G.add_edge(edge.outV.id, edge.inV.id)
    elif edge.label == 'requirement':
        G.add_edge(edge.inV.id, edge.outV.id)

# Draw the graph
pos = graphviz_layout(G, prog='dot', args='-Grankdir=LR')
#pos = nx.spring_layout(G)
labels = nx.get_node_attributes(G, 'name')

#types = nx.get_node_attributes(G, 'type')
node_size = [(5000 if labels[k] == 'Wish 1' else 3000) for k in G.nodes()]

#node_size = 4000
nx.draw(G, pos, with_labels=True, labels=labels, node_size=node_size, node_color='skyblue', font_size=10, font_color='black', font_weight='bold', edge_color='gray')
plt.show()

# Close the connection
connection.close()