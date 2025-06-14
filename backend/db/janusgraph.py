import warnings
import logging
from contextlib import contextmanager

from fastapi import HTTPException, Query
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order, P
from gremlin_python.structure.graph import Edge as GremlinEdge
from gremlin_python.structure.graph import Vertex as Gremlin_vertex
from janusgraph_python.driver.serializer import JanusGraphSONSerializersV3d0
from janusgraph_python.process.traversal import Text

from backend.models import (
    NodeBase,
    EdgeBase,
    SubgraphBase,
    NodeId,
    PartialNodeBase,
    EdgeBase,
)
from backend.properties import NodeStatus
from backend.db.base import GraphDatabaseInterface


class JanusGraphDB(GraphDatabaseInterface):
    def __init__(self, host: str, traversal_source: str):
        super().__init__()
        self.host = host
        self.traversal_source = traversal_source
        self.logger.info(
            f"Initialized JanusGraphDB with host: {host} and traversal source: {traversal_source}"
        )

    @contextmanager
    def connection(self):
        connection = DriverRemoteConnection(
            f"ws://{self.host}:8182/gremlin",
            self.traversal_source,
            message_serializer=JanusGraphSONSerializersV3d0(),
        )
        g = traversal().with_remote(connection)
        try:
            yield g
        finally:
            connection.close()

    def get_whole_graph(self) -> SubgraphBase:
        with self.connection() as g:
            nodes = [convert_gremlin_vertex(vertex) for vertex in g.V().to_list()]
            edges = [convert_gremlin_edge(edge) for edge in g.E().to_list()]
        return SubgraphBase(nodes=nodes, edges=edges)

    def get_graph_summary(self) -> dict:
        with self.connection() as g:
            vertex_count = g.V().count().next()
            edge_count = g.E().count().next()
        return {"nodes": vertex_count, "edges": edge_count}

    def reset_whole_graph(self) -> None:
        with self.connection() as g:
            warnings.warn("Deleting all nodes and edges in the database!")
            g.V().drop().iterate()

    def update_graph(self, subgraph: SubgraphBase) -> SubgraphBase:
        with self.connection() as g:
            mapping = {}
            nodes_out = []
            edges_out = []
            for node in subgraph.nodes:
                try:
                    if (
                        node.node_id is not None and g.V(node.node_id).has_next()
                    ):  # TODO: node_id shouldn't be none!
                        # update node
                        node_out = convert_gremlin_vertex(
                            self.update_gremlin_node(node)
                        )
                    else:
                        # create node
                        node_out = convert_gremlin_vertex(
                            self.create_gremlin_node(node)
                        )
                        # node_out.id_from_ui = (
                        #     node.node_id
                        # )
                        mapping[node.node_id] = node_out.node_id
                    nodes_out.append(node_out)
                except StopIteration:
                    ...
            for edge in subgraph.edges:
                try:
                    if (
                        g.V(edge.source)
                        .out_e(edge.edge_type)
                        .where(__.inV().has_id(edge.target))
                        .has_next()
                    ):
                        # update edge
                        edge_out = convert_gremlin_edge(self.update_gremlin_edge(edge))
                    else:
                        # create edge
                        update_edge_source_from = None
                        update_edge_target_from = None
                        if edge.source in mapping:
                            update_edge_source_from = edge.source
                            edge.source = mapping[edge.source]
                        if edge.target in mapping:
                            update_edge_target_from = edge.target
                            edge.target = mapping[edge.target]
                        edge_out = convert_gremlin_edge(self.create_gremlin_edge(edge))
                        edge_out.source_from_ui = update_edge_source_from
                        edge_out.target_from_ui = update_edge_target_from
                    edges_out.append(edge_out)
                except StopIteration:
                    ...

            return {"nodes": nodes_out, "edges": edges_out}

    def get_induced_subgraph(self, node_id: int, levels: int) -> SubgraphBase:
        with self.connection() as g:
            try:
                # Start traversal from the given node
                trav = g.V(node_id).repeat(__.both_e().both_v()).times(levels).dedup()
                vertices = trav.to_list()

                if not vertices:
                    vertex = g.V(node_id).next()
                    return {"nodes": [convert_gremlin_vertex(vertex)], "edges": []}

                # Collect edges separately
                edge_trav = (
                    g.V(node_id)
                    .repeat(__.both_e().both_v())
                    .times(levels)
                    .dedup()
                    .both_e()
                    .dedup()
                )
                edges = edge_trav.to_list()

                # Convert vertices and edges to the appropriate data models
                nodes = [convert_gremlin_vertex(vertex) for vertex in vertices]
                edges = [convert_gremlin_edge(edge) for edge in edges]
                return {"nodes": nodes, "edges": edges}
            except StopIteration:
                raise HTTPException(status_code=404, detail="Node not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def search_nodes(
        self,
        node_type: list[str] | str = Query(None),
        title: str | None = None,
        scope: str | None = None,
        status: list[NodeStatus] | NodeStatus = Query(None),
        tags: list[str] | None = Query(None),
        description: str | None = None,
    ) -> list[NodeBase]:
        with self.connection() as g:
            trav = g.V()
            if node_type is not None:
                if isinstance(node_type, list):
                    trav = trav.has("node_type", P.within(node_type))
                elif isinstance(node_type, str):
                    trav = trav.has("node_type", node_type)
            if title:
                for word in title.split(" "):
                    trav = trav.has("title", Text.text_contains_fuzzy(word))
                # trav = trav.has("title", Text.text_fuzzy(title))           # in-memory which can be costly
            if scope:
                for word in scope.split(" "):
                    trav = trav.has("scope", Text.text_contains_fuzzy(scope))
            if status is not None:
                if isinstance(status, list):
                    trav = trav.has("status", P.within(status))
                elif isinstance(status, NodeStatus):
                    trav = trav.has("status", status)
            if tags:
                for tag in tags:
                    trav = trav.has(
                        "tags", Text.text_contains_fuzzy(tag)
                    )  # Ok for now because tags is parsed as string
            if description:
                for word in description.split(" "):
                    trav = trav.has("description", Text.text_contains_fuzzy(word))
            return [convert_gremlin_vertex(node) for node in trav.to_list()]

    def get_random_node(self, node_type: str = None) -> NodeBase:
        with self.connection() as g:
            try:
                trav = g.V()
                if node_type is not None:
                    trav = trav.has_label(node_type)
                vertex = trav.order().by(Order.shuffle).limit(1).next()
            except StopIteration:
                if node_type is not None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Error fetching a random node of type {node_type}, there may be no node in the database",
                    )
                raise HTTPException(
                    status_code=404,
                    detail="Error fetching a random node, there may be no node in the database",
                )
            return convert_gremlin_vertex(vertex)

    def get_node(self, node_id: int) -> NodeBase:
        with self.connection() as g:
            try:
                vertex = g.V(node_id).next()
            except StopIteration:
                raise HTTPException(status_code=404, detail="Node not found")
            return convert_gremlin_vertex(vertex)

    def create_node(self, node: NodeBase) -> NodeBase:
        with self.connection() as g:
            # TODO: Check for possible duplicates
            created_node = self.create_gremlin_node(node)
            return convert_gremlin_vertex(created_node)

    def delete_node(self, node_id: int) -> None:
        with self.connection() as g:
            if not g.V(node_id).has_next():
                raise HTTPException(status_code=404, detail="Node not found")

            g.V(node_id).both_e().drop().iterate()
            g.V(node_id).drop().iterate()
            return {"message": "Node deleted"}

    def update_node(self, node: NodeBase) -> NodeBase:
        with self.connection() as g:
            if not g.V(node.node_id).has_next():
                raise HTTPException(status_code=404, detail="Node not found")
            gremlin_vertex = self.update_gremlin_node(node)
            return convert_gremlin_vertex(gremlin_vertex)

    def get_edge_list(self) -> list[EdgeBase]:
        with self.connection() as g:
            return [
                convert_gremlin_edge(edge)
                for edge in g.E().to_list()
                if edge is not None
            ]

    def get_edge(self, source_id: int, target_id: int) -> EdgeBase:
        with self.connection() as g:
            try:
                traversal = g.V(source_id).out_e().where(__.in_v().has_id(target_id))
                edge = traversal.next()
                return convert_gremlin_edge(edge)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Edge not found")

    def find_edges(
        self,
        source_id: NodeId = None,
        target_id: NodeId = None,
        edge_type: str = None,
    ) -> list[EdgeBase]:
        with self.connection() as g:
            try:
                # Start with a base traversal
                trav = g.E()

                # Add source condition if provided
                if source_id:
                    trav = trav.where(__.out_v().has_id(source_id))

                # Add target condition if provided
                if target_id:
                    trav = trav.where(__.in_v().has_id(target_id))

                # Add edge type condition if provided
                if edge_type:
                    trav = trav.has_label(edge_type)

                # Execute the traversal and convert to list
                edges = trav.to_list()

                # Check if edges are found
                if not edges:
                    return []

                return [convert_gremlin_edge(edge) for edge in edges]

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def create_edge(self, edge: EdgeBase) -> EdgeBase:
        with self.connection() as g:
            # TODO: Check for possible duplicates
            try:
                created_edge = self.create_gremlin_edge(edge)
                return convert_gremlin_edge(created_edge)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Node or edge not found")

    def delete_edge(
        self, source_id: int, target_id: int, edge_type: str = None
    ) -> None:
        with self.connection() as g:
            # logging.info(f"Attempting to delete edge from {source_id} to {target_id} with edge_type {edge_type}")
            trav = g.V(source_id)
            try:
                if edge_type is not None:
                    trav = trav.out_e(edge_type).where(__.in_v().has_id(target_id))
                else:
                    warnings.warn(
                        "No edge type provided, deleting all edges from source to target"
                    )
                    trav = trav.out_e().where(__.in_v().has_id(target_id))
                # logging.info(f"Traversal query: {trav}")
                trav.drop().iterate()
                return {"message": "Edge deleted"}
            except StopIteration:
                logging.error(f"Edge from {source_id} to {target_id} not found")
                raise HTTPException(status_code=404, detail="Edge not found")

    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        with self.connection() as g:
            try:
                if not self.exists_edge_in_db(edge):
                    raise HTTPException(status_code=404, detail="Edge not found")
                gremlin_edge = self.update_gremlin_edge(edge)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Error updating edge")

            return convert_gremlin_edge(gremlin_edge)

    # UTILS
    def create_gremlin_node(self, node: NodeBase) -> Gremlin_vertex:
        """Create a gremlin vertex in the database."""
        with self.connection() as g:
            created_node = g.add_v()
            # if node.node_id is not None:
            #    created_node = created_node.property(T.id, UUID(long=node.node_id))
            for p in NodeBase.get_single_field_types():
                created_node = created_node.property(p, getattr(node, p))
            for p in NodeBase.get_list_field_types():
                created_node = created_node.property(p, parse_list(getattr(node, p)))
            return created_node.next()

    def create_gremlin_edge(self, edge: EdgeBase) -> GremlinEdge:
        """Create a gremlin edge in the database."""
        with self.connection() as g:
            created_edge = g.V(edge.source).add_e(edge.edge_type)
            for p in EdgeBase.get_single_field_types():
                created_edge = created_edge.property(p, getattr(edge, p))
            for p in EdgeBase.get_list_field_types():
                created_edge = created_edge.property(p, parse_list(getattr(edge, p)))
            created_edge = created_edge.to(__.V(edge.target))
            return created_edge.next()

    def exists_edge_in_db(self, edge: EdgeBase) -> bool:
        """Check if an edge exists in the database."""
        with self.connection() as g:
            return (
                g.V(edge.source)
                .out_e(edge.edge_type)
                .where(__.in_v().has_id(edge.target))
                .has_next()
            )

    def update_gremlin_node(self, node: PartialNodeBase) -> Gremlin_vertex | None:
        """Update the properties of a node defined by its ID."""
        with self.connection() as g:
            updated_node = g.V(node.node_id)
            for p in NodeBase.get_single_field_types():
                if getattr(node, p) is not None:
                    updated_node = updated_node.property(p, getattr(node, p))
            for p in NodeBase.get_list_field_types():
                if getattr(node, p) is not None:
                    updated_node = updated_node.property(
                        p, parse_list(getattr(node, p))
                    )
            return updated_node.next()

    def update_gremlin_edge(self, edge: EdgeBase) -> GremlinEdge:
        """Update the properties of an edge defined by its source and target nodes."""
        with self.connection() as g:
            # TODO: test if any change is made and deal with mere additions
            if edge.edge_type is not None:
                updated_edge = (
                    g.V(edge.source)
                    .out_e(edge.edge_type)
                    .where(__.in_v().has_id(edge.target))
                )
            else:
                updated_edge = (
                    g.V(edge.source).outE().where(__.inV().hasId(edge.target))
                )
            for p in EdgeBase.get_single_field_types():
                updated_edge = updated_edge.property(p, getattr(edge, p))
            for p in EdgeBase.get_list_field_types():
                updated_edge = updated_edge.property(p, parse_list(getattr(edge, p)))
            return updated_edge.next()

    def migrate_label_to_property(self, property_name: str) -> None:
        try:
            with self.connection() as g:
                vertices = g.V().to_list()
                print(f"Found {len(vertices)} vertices to migrate.")
                for vertex in vertices:
                    print(f"Processing vertex: {vertex}")
                    label = vertex.label
                    print(f"Label obtained: {label}")
                    migration_step = g.V(vertex.id).property(property_name, label)
                    print(f"Migration step: {migration_step}")
                    migration_step.iterate()
                    print(f"Vertex {vertex.id} migrated.")
            logging.info(f"Successfully migrated labels to property {property_name}")
            print(f"Successfully migrated labels to property {property_name}")
        except Exception as e:
            print(f"Error during migration: {e}")  # Added line
            raise e


# Utils


def parse_list(l: list[str]) -> str | None:
    if len(l) == 0:
        return None
    if len(l) > 1:
        warnings.warn(
            "list properties are experimental and currently only supported with separator ;"
        )
    return ";".join(l)


def unparse_stringlist(s: str) -> list[str]:
    return s.split(";")


def convert_gremlin_vertex(vertex: Gremlin_vertex) -> NodeBase:
    """Convert a gremlin vertex to a NodeBase object."""
    d = dict()
    d["node_id"] = vertex.id
    # if vertex.label is not None:
    #     d["node_type"] = vertex.label
    if vertex.properties is not None:
        for p in vertex.properties:
            if p.key in NodeBase.get_list_field_types():
                d[p.key] = unparse_stringlist(p.value)
            elif p.key in NodeBase.get_single_field_types():
                d[p.key] = p.value
            else:
                warnings.warn(f"invalid node property: {p.key}")
    return NodeBase(**d)


def convert_gremlin_edge(edge) -> EdgeBase:
    """Convert a gremlin edge to an EdgeBase object."""
    d = dict()
    d["source"] = edge.outV.id
    d["target"] = edge.inV.id
    d["edge_type"] = edge.label
    if edge.properties is not None:
        for p in edge.properties:
            if p.key in EdgeBase.get_list_field_types():
                d[p.key] = unparse_stringlist(p.value)
            elif p.key in EdgeBase.get_single_field_types():
                d[p.key] = p.value
            else:
                warnings.warn(f"invalid edge property: {p.key}")
    return EdgeBase(**d)
