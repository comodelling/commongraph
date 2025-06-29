from typing import List
import random
import logging

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, select
from fastapi import HTTPException, Query

from backend.db.base import (
    UserDatabaseInterface,
    GraphHistoryRelationalInterface,
    RatingHistoryRelationalInterface,
)
from backend.models.base import (
    NodeBase,
    EdgeBase,
    SubgraphBase,
)
from backend.models.fixed import (
    NodeId,
    User,
    UserRead,
    UserCreate,
    GraphHistoryEvent,
    EntityType,
    EntityState,
    RatingEvent,
)
from backend.properties import NodeStatus
from backend.models.dynamic import NodeTypeModels, EdgeTypeModels, DynamicSubgraph
from backend.utils.security import hash_password
from backend.db.config import get_engine

# logger in debug mode
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
                is_active=user.is_active,
                is_admin=user.is_admin,
            )
            session.add(db_user)
            try:
                session.commit()
                session.refresh(db_user)
            except IntegrityError:
                session.rollback()
                raise HTTPException(status_code=400, detail="User already exists")
            return UserRead(
                username=db_user.username,
                preferences=db_user.preferences,
                is_active=db_user.is_active,
                is_admin=db_user.is_admin,
            )

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
            return UserRead(
                username=user.username,
                preferences=user.preferences,
                is_active=user.is_active,
                is_admin=user.is_admin,
            )

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
            return UserRead(
                username=user.username,
                preferences=user.preferences,
                is_active=user.is_active,
                is_admin=user.is_admin,
            )

    def reset_user_table(self):
        """Reset the database by dropping all tables and recreating them."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

    def list_users(self) -> List[UserRead]:
        """Fetch and return all users as UserRead."""
        with Session(self.engine) as session:
            statement = select(User)
            results = session.exec(statement).all()
            return [
                UserRead(
                    username=u.username,
                    preferences=u.preferences,
                    is_active=u.is_active,
                    is_admin=u.is_admin,
                )
                for u in results
            ]


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
                self.logger.debug(
                    f"Logged rating by {rating.username} for {rating.entity_type}"
                )
            return rating

    def get_node_rating(
        self, node_id: int, poll_label: str, username: str
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
                    RatingEvent.poll_label == poll_label,
                    RatingEvent.username == username,
                )
                .order_by(RatingEvent.timestamp.desc())
            )

            rating = session.exec(statement).first()
            return rating

    def get_node_ratings(
        self, node_id: int, poll_label: str
    ) -> list[RatingEvent]:
        """
        Retrieve the most recent rating per user for a given node using PostgreSQL's DISTINCT ON.
        """
        print(RatingEvent.__tablename__)
        query = text(
            f"""
            SELECT DISTINCT ON (username) *
            FROM {RatingEvent.__tablename__}
            WHERE entity_type = :entity_type
              AND node_id = :node_id
              AND poll_label = :poll_label
            ORDER BY username, timestamp DESC
        """
        )
        params = {
            "entity_type": EntityType.node,
            "node_id": node_id,
            "poll_label": poll_label,
        }
        with Session(self.engine) as session:
            results = session.exec(query, params=params).fetchall()
            return [RatingEvent.model_validate(row) for row in results]

    def get_nodes_ratings(
        self, node_ids: list[NodeId], poll_label: str
    ) -> dict[NodeId, list[RatingEvent]]:
        """
        Retrieve the most recent rating per user for multiple nodes.
        Returns a dictionary mapping each node_id to a list of RatingEvent,
        where each rating represents the latest rating by a user.
        """
        query = text(
            f"""
            WITH latest AS (
                SELECT DISTINCT ON (node_id, username) *
                FROM {RatingEvent.__tablename__}
                WHERE entity_type = :entity_type
                AND node_id = ANY(:node_ids)
                AND poll_label = :poll_label
                ORDER BY node_id, username, timestamp DESC
            )
            SELECT * FROM latest;
            """
        )
        params = {
            "entity_type": EntityType.node,
            "node_ids": node_ids,
            "poll_label": poll_label,
        }
        with Session(self.engine) as session:
            rows = session.exec(query, params=params).fetchall()
            result: dict[int, list[RatingEvent]] = {}
            for row in rows:
                rating = RatingEvent.model_validate(row)
                result.setdefault(rating.node_id, []).append(rating)
            return result

    def get_edge_rating(
        self, source_id: int, target_id: int, poll_label: str, username: str
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
                    RatingEvent.poll_label == poll_label,
                    RatingEvent.username == username,
                )
                .order_by(RatingEvent.timestamp.desc())
            )
            rating = session.exec(statement).first()
            return rating

    def get_node_median_rating(
        self, node_id: int, poll_label: str
    ) -> float | None:
        """
        Compute the median rating for a node + poll_label,
        considering only each user’s latest rating.
        """
        with Session(self.engine) as session:
            stmt = text(f"""
            SELECT percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY rating) AS median
                FROM (
                SELECT DISTINCT ON (username) rating
                    FROM {RatingEvent.__tablename__}
                WHERE entity_type = :etype
                    AND node_id    = :nid
                    AND poll_label = :pl
                ORDER BY username, timestamp DESC
                ) AS latest;
            """)
            result = session.exec(
                stmt,
                params={
                    "etype": EntityType.node.value,
                    "nid": node_id,
                    "pl": poll_label,
                },
            )
            row = result.first()
            return row.median if row and row.median is not None else None

    def get_edge_ratings(
        self, source_id: int, target_id: int, poll_label: str
    ) -> list[RatingEvent]:
        """
        Retrieve the most recent rating per user for a given edge using PostgreSQL's DISTINCT ON.
        """
        query = text(
            f"""
            SELECT DISTINCT ON (username) *
            FROM {RatingEvent.__tablename__}
            WHERE entity_type = :entity_type
              AND source_id = :source_id
              AND target_id = :target_id
              AND poll_label = :poll_label
            ORDER BY username, timestamp DESC
        """
        )
        params = {
            "entity_type": EntityType.edge,
            "source_id": source_id,
            "target_id": target_id,
            "poll_label": poll_label,
        }
        with Session(self.engine) as session:
            results = session.exec(query, params=params).fetchall()
            return [RatingEvent.model_validate(row) for row in results]

    def get_edge_median_rating(
        self, source_id: int, target_id: int, poll_label: str
    ) -> float | None:
        """
        Compute the median rating for an edge + poll_label,
        considering only each user’s latest rating.
        """
        with Session(self.engine) as session:
            stmt = text(f"""
            SELECT percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY rating) AS median
                FROM (
                SELECT DISTINCT ON (username) rating
                    FROM {RatingEvent.__tablename__}
                WHERE entity_type = :etype
                    AND source_id  = :sid
                    AND target_id  = :tid
                    AND poll_label = :pl
                ORDER BY username, timestamp DESC
                ) AS latest;
            """)
            row = session.exec(
                stmt,
                params={
                    "etype": EntityType.edge.value,
                    "sid": source_id,
                    "tid": target_id,
                    "pl": poll_label,
                },
            ).first()
            return row.median if row and row.median is not None else None

    def get_nodes_median_ratings(
        self, node_ids: list[NodeId], poll_label: str
    ) -> dict[NodeId, float | None]:
        """
        Compute per‐node median over each user's latest rating, in one query.
        """
        if not node_ids:
            return {}
        with Session(self.engine) as session:
            stmt = text(f"""
              SELECT node_id,
                     percentile_cont(0.5)
                       WITHIN GROUP (ORDER BY rating) AS median
                FROM (
                  SELECT DISTINCT ON (node_id, username)
                         node_id, username, rating
                    FROM {RatingEvent.__tablename__}
                   WHERE entity_type = :etype
                     AND poll_label = :pl
                     AND node_id IN :nids
                   ORDER BY node_id, username, timestamp DESC
                ) AS latest
               GROUP BY node_id;
            """)
            rows = session.exec(
                stmt,
                params={
                  "etype": EntityType.node.value,
                  "pl": poll_label,
                  "nids": tuple(node_ids),
                },
            ).all()
            # map missing ids → None
            result = {nid: None for nid in node_ids}
            for r in rows:
                result[r.node_id] = r.median
            return result

    def get_edges_ratings(
        self,
        edges: list[tuple[int, int]],
        poll_label: str,
    ) -> dict[tuple[int, int], list[RatingEvent]]:
        """
        Retrieve the most recent rating per user for a set of edges in one query
        using PostgreSQL's DISTINCT ON. Returns a dict keyed by (source_id, target_id),
        where each value is a list of the latest RatingEvents by user for that edge.
        """
        if not edges:
            return {}

        # Transform list[tuple[int,int]] -> a list of composite pairs. If your DB driver
        # doesn't allow passing a tuple directly as a parameter, you can adapt to strings
        # or use a temporary table, etc.
        # For example, you can pass something like an array of text "source-target" and
        # parse it in SQL, or try matching in a WHERE (source_id, target_id) IN (...).
        # Below is a small trick constructing a VALUES list for the edge pairs.
        edge_values = ", ".join(f"({source},{target})" for (source, target) in edges)

        query = text(
            f"""
            WITH latest AS (
                SELECT DISTINCT ON (source_id, target_id, username) *
                FROM {RatingEvent.__tablename__}
                WHERE entity_type = :entity_type
                  AND poll_label = :poll_label
                  AND (source_id, target_id) IN (
                      {edge_values}
                  )
                ORDER BY source_id, target_id, username, timestamp DESC
            )
            SELECT * FROM latest;
        """
        )

        params = {
            "entity_type": EntityType.edge,
            "poll_label": poll_label,
        }

        with Session(self.engine) as session:
            rows = session.exec(query, params=params).fetchall()

        # Group them by (source_id, target_id)
        results: dict[tuple[int, int], list[RatingEvent]] = {}
        for row in rows:
            rating = RatingEvent.model_validate(row)
            edge_key = (rating.source_id, rating.target_id)
            results.setdefault(edge_key, []).append(rating)

        return results

    def get_edges_median_ratings(
        self,
        edges: list[tuple[int, int]],
        poll_label: str,
    ) -> dict[tuple[int, int], float | None]:
        """
        Compute per‐edge median over each user's latest rating, in one query.
        """
        if not edges:
            return {}
        with Session(self.engine) as session:
            stmt = text(f"""
              SELECT source_id, target_id,
                     percentile_cont(0.5)
                       WITHIN GROUP (ORDER BY rating) AS median
                FROM (
                  SELECT DISTINCT ON (source_id, target_id, username)
                         source_id, target_id, username, rating
                    FROM {RatingEvent.__tablename__}
                   WHERE entity_type = :etype
                     AND poll_label = :pl
                     AND (source_id, target_id) IN :pairs
                   ORDER BY source_id, target_id, username, timestamp DESC
                ) AS latest
               GROUP BY source_id, target_id;
            """)
            rows = session.exec(
                stmt,
                params={
                  "etype": EntityType.edge.value,
                  "pl": poll_label,
                  "pairs": tuple(edges),
                },
            ).all()
            result = {(s, t): None for s, t in edges}
            for r in rows:
                result[(r.source_id, r.target_id)] = r.median
            return result


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
        data = dict(payload or {})
        # ensure minimal defaults
        #data.setdefault("node_type", "potentiality")  #TODO: check defaults
        #data.setdefault("scope", "")
        try:
            nt = data["node_type"]
        except KeyError as e:
            logger.error(f'"node_type" not found in payload: {data}')
            raise e
        Dyn = NodeTypeModels.get(nt)
        if Dyn:
            # Dyn is a SQLModel subclass with only your config-allowed fields
            logger.debug('blablablabla\n')
            out = Dyn(**data)
            logger.info(f"Using dynamic model for node type: {nt}, ending up in {out}")
            return out
        # fallback
        return NodeBase.model_validate(data)

    def _to_edge(self, obj) -> EdgeBase:
        data = obj if isinstance(obj, dict) else obj.model_dump()
        et = data.get("edge_type")
        Dyn = EdgeTypeModels.get(et)
        if Dyn:
            return Dyn(**data)
        return EdgeBase.model_validate(data)

    def get_whole_graph(self) -> SubgraphBase:
        """Reconstruct the current graph from the latest events."""
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

            nodes = []
            for event in nodes_latest.values():
                if event.state == EntityState.deleted:
                    continue
                if event.payload['node_type'] not in NodeTypeModels:
                    # Handle orphaned nodes with types that no longer exist
                    self.logger.warning(
                        f"Node {event.node_id} has an unknown type: {event.payload['node_type']}"
                    )
                    continue
                nodes.append(self._to_node(event.payload))

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
            edges = []
            for event in edges_latest.values():
                if event.state == EntityState.deleted:
                    continue
                if event.payload['edge_type'] not in EdgeTypeModels:
                    # Handle orphaned edges with types that no longer exist
                    self.logger.warning(
                        f"Edge {event.source_id} -> {event.target_id} has an unknown type: {event.payload['edge_type']}"
                    )
                    continue
                edges += [self._to_edge(event.payload)]

            self.logger.info(
                f"Returning graph with {len(nodes)} nodes and {len(edges)} edges"
            )
            return DynamicSubgraph(nodes=nodes, edges=edges)

    def get_graph_summary(self) -> dict:
        graph = self.get_whole_graph()
        return {"nodes": len(graph.nodes), "edges": len(graph.edges)}

    def reset_whole_graph(self, username: str = "system") -> None:
        """Reset the graph by clearing all history events."""
        from sqlalchemy import delete

        with Session(self.engine) as session:
            session.exec(delete(GraphHistoryEvent))
            session.commit()

    def update_graph(self, subgraph: SubgraphBase, username: str = "system") -> SubgraphBase:
        """
        Update the subgraph by iterating over nodes and edges.
        For each node, if it exists (by node_id), update it; otherwise, create it.
        For each edge, if it exists (by source and target), update it; otherwise, create it.
        Applies mapping for newly created nodes.
        """
        mapping: dict[int, int] = {}
        nodes_out = []
        for node in subgraph.nodes:
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
        for edge in subgraph.edges:
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

        return DynamicSubgraph(nodes=nodes_out, edges=edges_out)

    def get_induced_subgraph(self, node_id: NodeId, levels: int) -> SubgraphBase:
        """
        Reconstruct an induced subgraph starting from node_id by performing a BFS.
        """
        whole = self.get_whole_graph()
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
        return DynamicSubgraph(nodes=list(induced_nodes.values()), edges=induced_edges)

    def search_nodes(
        self,
        node_type: list[str] | str = Query(None),
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
        graph = self.get_whole_graph()
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

        for node in graph.nodes:
            self.logger.debug(
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

    def get_random_node(self, node_type: str = None) -> NodeBase:
        nodes = self.get_whole_graph().nodes
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
        edge_type: str = None,
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
