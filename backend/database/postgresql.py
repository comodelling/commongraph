from typing import List
import random

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, select
from fastapi import HTTPException, Query

from .base import (
    UserDatabaseInterface,
    GraphHistoryRelationalInterface,
    RatingHistoryRelationalInterface,
)
from models import (
    NodeBase,
    EdgeBase,
    NodeId,
    NodeType,
    NodeStatus,
    EdgeType,
    LikertScale,
    User,
    UserRead,
    UserCreate,
    GraphHistoryEvent,
    Subnet,
    EntityType,
    EntityState,
    RatingEvent,
    RatingType,
)
from utils.security import hash_password
from database.config import get_engine


class UserPostgreSQLDB(UserDatabaseInterface):
    def __init__(self, database_url: str):
        super().__init__()
        self.engine = get_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_user(self, user: UserCreate) -> UserRead:
        with Session(self.engine) as session:
            hashed_password = hash_password(user.password)
            db_user = User(
                username=user.username,
                password=hashed_password,
                preferences=user.preferences,
                security_question=user.security_question,
                security_answer=user.security_answer,
            )
            session.add(db_user)
            try:
                session.commit()
                session.refresh(db_user)
            except IntegrityError:
                session.rollback()
                raise HTTPException(status_code=400, detail="User already exists")
            return UserRead(username=db_user.username, preferences=db_user.preferences)

    def get_user(self, username: str) -> User | None:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            result = session.exec(statement).first()
            return result

    def update_user(self, user: User) -> UserRead:
        with Session(self.engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserRead(username=user.username, preferences=user.preferences)

    def update_preferences(self, username: str, new_prefs: dict) -> UserRead:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            user = session.exec(statement).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            # Ensure preferences is a dict (or JSON) to update
            if not user.preferences:
                user.preferences = {}
            self.logger.info(f"Current preferences before update: {user.preferences}")
            # user.preferences.update(new_prefs)
            user.preferences = {**user.preferences, **new_prefs}
            self.logger.info(f"New preferences to be updated: {new_prefs}")
            self.logger.info(f"Updated preferences after merge: {user.preferences}")
            session.add(user)
            session.commit()
            session.refresh(user)
            self.logger.info(
                f"Final preferences in database after commit: {user.preferences}"
            )
            return UserRead(username=user.username, preferences=user.preferences)

    def reset_user_table(self):
        """Reset the database by dropping all tables and recreating them."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)


class RatingHistoryPostgreSQLDB(RatingHistoryRelationalInterface):
    def __init__(self, database_url: str):
        super().__init__()
        self.engine = get_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def reset_table(self):
        """Reset the database by dropping all tables and recreating them."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

    def log_rating(self, rating: RatingEvent) -> RatingEvent:
        """
        Log a rating for a given entity and user.
        """
        with Session(self.engine) as session:
            session.add(rating)
            session.commit()
            session.refresh(rating)
            if hasattr(self, "logger"):
                self.logger.info(
                    f"Logged rating by {rating.username} for {rating.entity_type}"
                )
            return rating

    def get_node_rating(
        self, node_id: int, rating_type: RatingType, username: str
    ) -> RatingEvent | None:
        """
        Retrieve the latest rating of a given node by a given user.
        """
        with Session(self.engine) as session:
            statement = (
                select(RatingEvent)
                .where(
                    RatingEvent.entity_type == EntityType.node,
                    RatingEvent.node_id == node_id,
                    RatingEvent.rating_type == rating_type,
                    RatingEvent.username == username,
                )
                .order_by(RatingEvent.timestamp.desc())
            )

            rating = session.exec(statement).first()
            return rating

    def get_edge_rating(
        self, source_id: int, target_id: int, rating_type: RatingType, username: str
    ) -> RatingEvent | None:
        """
        Retrieve the latest rating of a given edge by a given user.
        """
        with Session(self.engine) as session:
            statement = (
                select(RatingEvent)
                .where(
                    RatingEvent.entity_type == EntityType.edge,
                    RatingEvent.source_id == source_id,
                    RatingEvent.target_id == target_id,
                    RatingEvent.rating_type == rating_type,
                    RatingEvent.username == username,
                )
                .order_by(RatingEvent.timestamp.desc())
            )
            rating = session.exec(statement).first()
            return rating

    def get_node_median_rating(
        self, node_id: int, rating_type: RatingType
    ) -> LikertScale | None:
        """
        Retrieve the median of latest ratings (LikertScale) for a given node.
        """
        with Session(self.engine) as session:
            statement = (
                select(RatingEvent)
                .where(
                    RatingEvent.entity_type == EntityType.node,
                    RatingEvent.node_id == node_id,
                    RatingEvent.rating_type == rating_type,
                )
                .order_by(RatingEvent.timestamp.desc())
            )
            ratings = session.exec(statement).all()
            if not ratings:
                raise HTTPException(status_code=404, detail="No ratings found for node")
            scale_order = [
                LikertScale.a,
                LikertScale.b,
                LikertScale.c,
                LikertScale.d,
                LikertScale.e,
            ]
            # Convert ratings to their index values
            indices = [scale_order.index(r.rating) for r in ratings]
            indices.sort()
            # Compute median index using the lower median in case of even count.
            mid = len(indices) // 2
            median_index = indices[mid] if len(indices) % 2 == 1 else indices[mid - 1]
            median_rating = scale_order[median_index]
            if hasattr(self, "logger"):
                self.logger.info(
                    f"Computed median rating for node {node_id} is {median_rating}"
                )
            return median_rating

    def get_edge_median_rating(
        self, source_id: int, target_id: int, rating_type: RatingType
    ) -> LikertScale | None:
        """
        Retrieve the median of latest ratings (LikertScale) for a given edge.
        """
        with Session(self.engine) as session:
            statement = (
                select(RatingEvent)
                .where(
                    RatingEvent.entity_type == EntityType.edge,
                    RatingEvent.source_id == source_id,
                    RatingEvent.target_id == target_id,
                    RatingEvent.rating_type == rating_type,
                )
                .order_by(RatingEvent.timestamp.desc())
            )
            ratings = session.exec(statement).all()
            if not ratings:
                raise HTTPException(status_code=404, detail="No ratings found for edge")
            scale_order = [
                LikertScale.a,
                LikertScale.b,
                LikertScale.c,
                LikertScale.d,
                LikertScale.e,
            ]
            indices = [scale_order.index(r.rating) for r in ratings]
            indices.sort()
            mid = len(indices) // 2
            median_index = indices[mid] if len(indices) % 2 == 1 else indices[mid - 1]
            median_rating = scale_order[median_index]
            if hasattr(self, "logger"):
                self.logger.info(
                    f"Computed median rating for edge {source_id}->{target_id} is {median_rating}"
                )
            return median_rating


class GraphHistoryPostgreSQLDB(GraphHistoryRelationalInterface):
    def __init__(self, database_url: str):
        super().__init__()
        self.engine = get_engine(database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def log_event(self, event: GraphHistoryEvent) -> GraphHistoryEvent:
        with Session(self.engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
            self.logger.info(f"Logged event: {event.event_id}")
            return event

    def get_node_history(self, node_id: NodeId) -> List[GraphHistoryEvent]:
        with Session(self.engine) as session:
            statement = select(GraphHistoryEvent).where(
                GraphHistoryEvent.node_id == node_id
            )
            events = session.exec(statement).all()
            self.logger.info(f"Found {len(events)} events for node: {node_id}")
            return events

    def get_edge_history(
        self, source_id: NodeId, target_id: NodeId
    ) -> List[GraphHistoryEvent]:
        with Session(self.engine) as session:
            statement = select(GraphHistoryEvent).where(
                GraphHistoryEvent.source_id == source_id,
                GraphHistoryEvent.target_id == target_id,
            )
            events = session.exec(statement).all()
            self.logger.info(
                f"Found {len(events)} events for edge: {source_id} -> {target_id}"
            )
            return events

    def revert_to_event(self, event_id: int) -> None:
        # Implementation would depend on your event-sourcing mechanism.
        self.logger.info(f"Requested revert to event {event_id}")
        raise HTTPException(
            status_code=501, detail="Revert functionality not implemented yet."
        )

    def _to_dict(self, obj) -> dict:
        """Helper to convert SQLModel objects to dict if needed."""
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, "dict"):
            return obj.model_dump()
        return obj

    def _to_node(self, payload: dict) -> NodeBase:
        # Ensure required fields are set with safe defaults.
        data = dict(payload) if payload else {}
        if data.get("node_type") is None:
            data["node_type"] = NodeType.potentiality
        if data.get("scope") is None:
            data["scope"] = ""
        return NodeBase.model_validate(data)

    def _to_edge(self, obj) -> EdgeBase:
        """Convert payload to an EdgeBase instance."""
        data = self._to_dict(obj)
        return EdgeBase.model_validate(data)

    def get_whole_network(self) -> Subnet:
        """Reconstruct the current network from the latest events."""
        with Session(self.engine) as session:
            node_events = session.exec(
                select(GraphHistoryEvent).where(
                    GraphHistoryEvent.entity_type == EntityType.node
                )
            ).all()
            self.logger.info(f"Fetched {len(node_events)} node events")
            nodes_latest = {}
            for event in node_events:
                nid = event.node_id
                if (
                    nid not in nodes_latest
                    or event.timestamp > nodes_latest[nid].timestamp
                ):
                    nodes_latest[nid] = event

            nodes = [
                self._to_node(event.payload)
                for event in nodes_latest.values()
                if event.state != EntityState.deleted
            ]

            edge_events = session.exec(
                select(GraphHistoryEvent).where(
                    GraphHistoryEvent.entity_type == EntityType.edge
                )
            ).all()
            edges_latest = {}
            for event in edge_events:
                key = (event.source_id, event.target_id)
                if (
                    key not in edges_latest
                    or event.timestamp > edges_latest[key].timestamp
                ):
                    edges_latest[key] = event
            edges = [
                self._to_edge(event.payload)
                for event in edges_latest.values()
                if event.state != EntityState.deleted
            ]

            self.logger.info(
                f"Returning network with {len(nodes)} nodes and {len(edges)} edges"
            )
            return Subnet(nodes=nodes, edges=edges)

    def get_network_summary(self) -> dict:
        subnet = self.get_whole_network()
        return {"nodes": len(subnet.nodes), "edges": len(subnet.edges)}

    def reset_whole_network(self, username: str = "system") -> None:
        """Reset the network by clearing all history events."""
        from sqlalchemy import delete

        with Session(self.engine) as session:
            session.exec(delete(GraphHistoryEvent))
            session.commit()

    def update_subnet(self, subnet: Subnet, username: str = "system") -> Subnet:
        """
        Update the subnet by iterating over nodes and edges.
        For each node, if it exists (by node_id), update it; otherwise, create it.
        For each edge, if it exists (by source and target), update it; otherwise, create it.
        Applies mapping for newly created nodes.
        """
        mapping: dict[int, int] = {}
        nodes_out = []
        for node in subnet.nodes:
            if not isinstance(node, NodeBase):
                self.logger.error(f"Invalid node: {node}, ignoring it.")
                continue
            try:
                # Check if the node exists
                existing_node = self.get_node(node.node_id)
                updated_node = self.update_node(node, username=username)
            except HTTPException:
                # Node does not exist; create it.
                created_node = self.create_node(node, username=username)
                mapping[node.node_id] = created_node.node_id
                updated_node = created_node
            nodes_out.append(updated_node)

        edges_out = []
        for edge in subnet.edges:
            if (
                not isinstance(edge, EdgeBase)
                or not hasattr(edge, "source")
                or not hasattr(edge, "target")
            ):
                self.logger.error(f"Invalid edge: {edge}, ignoring it.")
                continue
            if edge.source in mapping:
                edge.source = mapping[edge.source]
            if edge.target in mapping:
                edge.target = mapping[edge.target]
            try:
                # Check if edge already exists
                existing_edge = self.get_edge(edge.source, edge.target)
                updated_edge = self.update_edge(edge, username=username)
            except HTTPException:
                # Edge does not exist; create it.
                updated_edge = self.create_edge(edge, username=username)
            edges_out.append(updated_edge)

        return Subnet(nodes=nodes_out, edges=edges_out)

    def get_induced_subnet(self, node_id: NodeId, levels: int) -> Subnet:
        """
        Reconstruct an induced subnet starting from node_id by performing a BFS.
        """
        whole = self.get_whole_network()
        node_index = {node.node_id: node for node in whole.nodes}
        adjacency = {node.node_id: set() for node in whole.nodes}
        for edge in whole.edges:
            src = edge.source
            tgt = edge.target
            if src in adjacency:
                adjacency[src].add(tgt)
            if tgt in adjacency:
                adjacency[tgt].add(src)  # Add reverse direction

        visited = set()
        queue = [(node_id, 0)]
        induced_nodes = {}
        while queue:
            current, lvl = queue.pop(0)
            if current in visited or lvl > levels:
                continue
            visited.add(current)
            if current in node_index:
                induced_nodes[current] = node_index[current]
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, lvl + 1))

        induced_edges = [
            edge
            for edge in whole.edges
            if edge.source in induced_nodes and edge.target in induced_nodes
        ]
        return Subnet(nodes=list(induced_nodes.values()), edges=induced_edges)

    def search_nodes(
        self,
        node_type: list[NodeType] | NodeType = Query(None),
        title: str | None = None,
        scope: str | None = None,
        status: list[NodeStatus] | NodeStatus = Query(None),
        tags: list[str] | None = Query(None),
        description: str | None = None,
    ) -> list[NodeBase]:
        """
        Retrieve nodes matching the given filters.
        For keys like title, scope, description, etc., perform case-insensitive
        substring matches. For node_type or status, accept single values or lists.
        """
        subnet = self.get_whole_network()
        results = []

        # Build a dict of non-null filters:
        all_filters = {
            "node_type": node_type,
            "title": title,
            "scope": scope,
            "status": status,
            "tags": tags,
            "description": description,
        }
        active_filters = {k: v for k, v in all_filters.items() if v is not None}

        for node in subnet.nodes:
            self.logger.info(
                f"Checking node {node.node_id} with title: {getattr(node, 'title', None)}"
            )
            match = True
            for key, value in active_filters.items():
                node_value = getattr(node, key, None)
                self.logger.info(f"Node {node.node_id} attribute {key}: {node_value}")

                # If the node has no corresponding attribute value, it can't match
                if node_value is None:
                    match = False
                    break

                # Handle lists vs. single values (e.g., node_type or status)
                if key in {"node_type", "status"}:
                    if isinstance(value, list):
                        if node_value not in value:
                            match = False
                            break
                    else:
                        if node_value != value:
                            match = False
                            break

                # Handle array of tags by checking if all are contained in node's tags
                elif key == "tags":
                    # node_value should be a list of strings
                    if not isinstance(node_value, list):
                        match = False
                        break
                    # Ensure each requested tag is in the node's tags
                    for tag in value:
                        if tag.lower() not in [t.lower() for t in node_value]:
                            match = False
                            break
                    if not match:
                        break

                # For text fields (title, scope, description), check for multi-word substring
                elif key in {"title", "scope", "description"} and isinstance(
                    value, str
                ):
                    for word in value.split():
                        if word.lower() not in node_value.lower():
                            match = False
                            break
                    if not match:
                        break

                # Fallback: if both are strings, do basic substring check
                elif isinstance(node_value, str) and isinstance(value, str):
                    if value.lower() not in node_value.lower():
                        match = False
                        break
                else:
                    # Otherwise do exact equality
                    if node_value != value:
                        match = False
                        break

            if match:
                results.append(node)

        self.logger.info(
            f"Search filter {active_filters} returned {len(results)} nodes"
        )
        return results

    def get_random_node(self, node_type: NodeType = None) -> NodeBase:
        nodes = self.get_whole_network().nodes
        if node_type is not None:
            nodes = [
                node for node in nodes if getattr(node, "node_type", None) == node_type
            ]
        if not nodes:
            raise HTTPException(
                status_code=404, detail="No node found matching criteria"
            )
        return random.choice(nodes)

    def get_node(self, node_id: NodeId) -> NodeBase:
        with Session(self.engine) as session:
            stmt = (
                select(GraphHistoryEvent)
                .where(
                    GraphHistoryEvent.entity_type == EntityType.node,
                    GraphHistoryEvent.node_id == node_id,
                    GraphHistoryEvent.state != EntityState.deleted,
                )
                .order_by(GraphHistoryEvent.timestamp.desc())
            )
            event = session.exec(stmt).first()
            if not event:
                raise HTTPException(status_code=404, detail="Node not found")
            return self._to_node(event.payload)

    def create_node(self, node: NodeBase, username: str = "system") -> NodeBase:
        """
        Create a node by logging a creation event.
        'node' is a NodeBase instance, or convertible via .dict().
        """
        node_dict = self._to_dict(node)
        if not node_dict.get("node_id"):
            node_dict["node_id"] = random.randint(1, 10**6)
        event = GraphHistoryEvent(
            state=EntityState.created,
            entity_type=EntityType.node,
            node_id=node_dict.get("node_id"),
            payload=node_dict,
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.flush()  # ensure the event is handed over to the DB
            session.commit()
            session.refresh(event)
            self.logger.info(f"Created node event: {event}")
        return self._to_node(event.payload)

    def delete_node(self, node_id: NodeId, username: str = "system") -> None:
        # Verify node exists.
        try:
            self.get_node(node_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail="Node not found")
        event = GraphHistoryEvent(
            state=EntityState.deleted,
            entity_type=EntityType.node,
            node_id=node_id,
            payload={},  # empty payload for deletion
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.commit()

    def update_node(self, node: NodeBase, username: str = "system") -> NodeBase:
        """
        Update a node by merging new fields with the existing node so that
        required fields (e.g. node_type or scope) are preserved.
        """
        # Retrieve current node data.
        current = self.get_node(node.node_id)
        current_data = current.model_dump()
        new_data = self._to_dict(node)
        # Merge (new_data overrides current_data)
        merged = {**current_data, **new_data}
        event = GraphHistoryEvent(
            state=EntityState.updated,
            entity_type=EntityType.node,
            node_id=merged.get("node_id"),
            payload=merged,
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
        return self._to_node(event.payload)

    def get_edge_list(self) -> list[EdgeBase]:
        with Session(self.engine) as session:
            stmt = select(GraphHistoryEvent).where(
                GraphHistoryEvent.entity_type == EntityType.edge,
                GraphHistoryEvent.state != EntityState.deleted,
            )
            events = session.exec(stmt).all()
            edge_latest = {}
            for event in events:
                key = (event.source_id, event.target_id)
                if (
                    key not in edge_latest
                    or event.timestamp > edge_latest[key].timestamp
                ):
                    edge_latest[key] = event
            return [self._to_edge(event.payload) for event in edge_latest.values()]

    def get_edge(self, source_id: NodeId, target_id: NodeId) -> EdgeBase:
        with Session(self.engine) as session:
            stmt = (
                select(GraphHistoryEvent)
                .where(
                    GraphHistoryEvent.entity_type == EntityType.edge,
                    GraphHistoryEvent.source_id == source_id,
                    GraphHistoryEvent.target_id == target_id,
                )
                .order_by(GraphHistoryEvent.timestamp.desc())
            )
            event = session.exec(stmt).first()
            if not event or event.state == EntityState.deleted:
                raise HTTPException(status_code=404, detail="Edge not found")
            return self._to_edge(event.payload)

    def find_edges(self, **filters) -> list[EdgeBase]:
        """Find edges matching given filters."""
        edges = self.get_edge_list()
        results = []
        for edge in edges:
            match = True
            for key, value in filters.items():
                if getattr(edge, key, None) != value:
                    match = False
                    break
            if match:
                results.append(edge)
        return results

    def create_edge(self, edge: EdgeBase, username: str = "system") -> EdgeBase:
        """
        Create an edge by logging a creation event.
        Validate that both source and target nodes exist.
        """
        edge_dict = self._to_dict(edge)
        for node_id in (edge_dict.get("source"), edge_dict.get("target")):
            try:
                self.get_node(node_id)
            except HTTPException:
                raise HTTPException(
                    status_code=404, detail=f"Referenced node {node_id} not found"
                )
        event = GraphHistoryEvent(
            state=EntityState.created,
            entity_type=EntityType.edge,
            node_id=None,
            source_id=edge_dict.get("source"),
            target_id=edge_dict.get("target"),
            payload=edge_dict,
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
        return self._to_edge(event.payload)

    def delete_edge(
        self,
        source_id: NodeId,
        target_id: NodeId,
        edge_type: EdgeType = None,
        username: str = "system",
    ) -> None:
        event = GraphHistoryEvent(
            state=EntityState.deleted,
            entity_type=EntityType.edge,
            node_id=None,
            source_id=source_id,
            target_id=target_id,
            payload={},
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.commit()

    def update_edge(self, edge: EdgeBase, username: str = "system") -> EdgeBase:
        """
        Update an edge by logging an update event.
        'edge' is an EdgeBase instance.
        """
        edge_dict = self._to_dict(edge)
        event = GraphHistoryEvent(
            state=EntityState.updated,
            entity_type=EntityType.edge,
            node_id=None,
            source_id=edge_dict.get("source"),
            target_id=edge_dict.get("target"),
            payload=edge_dict,
            username=username,
        )
        with Session(self.engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
        return self._to_edge(event.payload)
