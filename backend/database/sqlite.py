import random

import sqlite3
from typing import Type, Dict, Any, get_origin, get_args, List
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel

from models import NodeBase, EdgeBase, Subnet, PartialNodeBase, PartialEdgeBase
from .base import DatabaseInterface


def map_field_type_to_sqlite(field_type: type) -> str:
    type_mapping = {
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bool: "BOOLEAN",
    }
    # Remove the following line to maintain type mappings
    # type_mapping = {}
    return type_mapping.get(field_type, "TEXT")


class SQLiteDB(DatabaseInterface):
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.node_description = None
        self.edge_description = None
        self._initialize_db()
        self.logger.info(f"Initialized SQLiteDB with db_path: {db_path}")

    def _initialize_db(self):
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            self._create_or_update_table(cursor, "nodes", NodeBase)
            self._create_or_update_table(cursor, "edges", EdgeBase)
            conn.commit()
            self.node_description = cursor.execute(
                "SELECT * FROM nodes LIMIT 1"
            ).description
            self.edge_description = cursor.execute(
                "SELECT * FROM edges LIMIT 1"
            ).description
            self.logger.debug(f"Node description: {self.node_description}")
            self.logger.debug(f"Edge description: {self.edge_description}")

    def _create_or_update_table(self, cursor, table_name: str, model: Type[BaseModel]):
        create_table_sql = self.generate_sqlite_schema(table_name, model)
        cursor.execute(create_table_sql)

        # Get existing columns
        existing_columns = [
            col[1] for col in cursor.execute(f"PRAGMA table_info({table_name})")
        ]

        # Add new columns from model properties
        model_fields = model.get_field_types()
        for field, field_type in model_fields.items():
            if field not in existing_columns:
                sqlite_type = map_field_type_to_sqlite(field_type)
                cursor.execute(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{field}" {sqlite_type}'
                )

    def generate_sqlite_schema(self, table_name: str, model: Type[BaseModel]) -> str:
        field_types: Dict[str, type] = model.get_field_types()
        fields_def = []
        unique_constraints = []

        if table_name == "nodes":
            fields_def.append(f'"node_id" INTEGER PRIMARY KEY')
        elif table_name == "edges":
            fields_def.append(f'"source" INTEGER NOT NULL')
            fields_def.append(f'"target" INTEGER NOT NULL')
            fields_def.append(f'"edge_type" TEXT NOT NULL')

        for field, field_type in field_types.items():
            if issubclass(field_type, Enum):
                fields_def.append(f'"{field}" TEXT')
            else:
                sqlite_type = map_field_type_to_sqlite(field_type)
                fields_def.append(f'"{field}" {sqlite_type}')

        # Define unique constraints for edges
        if table_name == "edges":
            fields_def.append("UNIQUE(source, target, edge_type)")
            fields_def.append("FOREIGN KEY(source) REFERENCES nodes(node_id)")
            fields_def.append("FOREIGN KEY(target) REFERENCES nodes(node_id)")

        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                {", ".join(fields_def)}
            )
        """
        return create_table_sql

    def node_row_to_dict(self, row):
        if row is None:
            return {}
        columns = [column[0] for column in self.node_description]
        d = dict(zip(columns, row))
        d["node_id"] = d.get("node_id")

        if "tags" in d and d["tags"]:
            d["tags"] = d["tags"].split(";")
        else:
            d["tags"] = []
        if "references" in d and d["references"]:
            d["references"] = d["references"].split(";")
        else:
            d["references"] = []
        if "proponents" in d and d["proponents"]:
            d["proponents"] = d["proponents"].split(";")
        else:
            d["proponents"] = []
        return d

    def edge_row_to_dict(self, row):
        if row is None:
            return {}
        columns = [column[0] for column in self.edge_description]
        d = dict(zip(columns, row))
        d["source"] = d.get("source")
        d["target"] = d.get("target")
        d["edge_type"] = d.get("edge_type")
        if "references" in d and d["references"]:
            d["references"] = d["references"].split(";")
        else:
            d["references"] = []
        return d

    def serialize_field(self, field: str, field_type: type, value: Any) -> Any:
        """Serialize field value based on its type for SQLite storage."""
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return value.value if value else None
        if isinstance(value, list):
            return ";".join(value) if value else ""
        return value

    def deserialize_field(self, field: str, field_type: type, value: Any) -> Any:
        """Deserialize field value from SQLite storage to Python types."""

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin == list or origin == List:
            if isinstance(value, str):
                # Split the string by ';' and filter out any empty strings
                return [item for item in value.split(";") if item]
            else:
                # If the value is not a string (e.g., None), return an empty list
                return []

        # Handle Enum types
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            try:
                return field_type(value)
            except ValueError:
                self.logger.warning(
                    f"Invalid enum value '{value}' for field '{field}'."
                )
                return None

        # Handle other types
        if value is None:
            return None
        return value

    def get_whole_network(self) -> Subnet:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            nodes = cursor.execute("SELECT * FROM nodes").fetchall()
            edges = cursor.execute("SELECT * FROM edges").fetchall()
            return Subnet(
                nodes=[NodeBase(**self.node_row_to_dict(node)) for node in nodes],
                edges=[EdgeBase(**self.edge_row_to_dict(edge)) for edge in edges],
            )

    def get_network_summary(self) -> dict:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            node_count = cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            edge_count = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            return {"nodes": node_count, "edges": edge_count}

    def reset_whole_network(self) -> None:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM nodes")
            cursor.execute("DELETE FROM edges")
            conn.commit()

    def update_subnet(self, subnet: Subnet) -> Subnet:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            mapping = {}
            nodes_out = []
            edges_out = []
            for node in subnet.nodes:
                if node.node_id is not None:
                    cursor.execute(
                        "SELECT 1 FROM nodes WHERE node_id = ?", (node.node_id,)
                    )
                    if cursor.fetchone():
                        node_out = self.update_node(node)
                    else:
                        node_out = self.create_node(node)
                        # node_out.id_from_ui = node.node_id
                        mapping[node.node_id] = node_out.node_id
                else:
                    node_out = self.create_node(node)
                    mapping[node.node_id] = node_out.node_id
                nodes_out.append(node_out)

            for edge in subnet.edges:
                if edge.source in mapping:
                    edge.source = mapping[edge.source]
                if edge.target in mapping:
                    edge.target = mapping[edge.target]
                cursor.execute(
                    "SELECT 1 FROM edges WHERE source = ? AND target = ? AND edge_type = ?",
                    (edge.source, edge.target, edge.edge_type),
                )
                if cursor.fetchone():
                    edge_out = self.update_edge(edge)
                else:
                    edge_out = self.create_edge(edge)
                edges_out.append(edge_out)

            return Subnet(nodes=nodes_out, edges=edges_out)

    def get_induced_subnet(self, node_id: int, levels: int) -> Subnet:
        def fetch_neighbors(cursor, node_ids, level):
            if level == 0:
                return set(node_ids), []
            nodes = set(node_ids)
            edges = set()
            for node_id in node_ids:
                cursor.execute(
                    "SELECT * FROM edges WHERE source = ? OR target = ?",
                    (node_id, node_id),
                )
                new_edges = cursor.fetchall()
                edges = edges.union(new_edges)
                for edge in new_edges:
                    nodes.add(edge[1])  # source
                    nodes.add(edge[2])  # target
            next_nodes, next_edges = fetch_neighbors(cursor, nodes, level - 1)
            return nodes.union(next_nodes), edges.union(next_edges)

        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            initial_nodes = [node_id]
            nodes, edges = fetch_neighbors(cursor, initial_nodes, levels)
            nodes = cursor.execute(
                "SELECT * FROM nodes WHERE node_id IN ({})".format(
                    ",".join("?" * len(nodes))
                ),
                list(nodes),
            ).fetchall()
            return Subnet(
                nodes=[NodeBase(**self.node_row_to_dict(node)) for node in nodes],
                edges=[EdgeBase(**self.edge_row_to_dict(edge)) for edge in edges],
            )

    def search_nodes(self, **kwargs) -> list[NodeBase]:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM nodes WHERE 1=1"
            params = []
            if "node_type" in kwargs and kwargs["node_type"]:
                if isinstance(kwargs["node_type"], list):
                    query += " AND node_type IN ({})".format(
                        ",".join("?" * len(kwargs["node_type"]))
                    )
                    params.extend(kwargs["node_type"])
                else:
                    query += " AND node_type = ?"
                    params.append(kwargs["node_type"])
            if "title" in kwargs and kwargs["title"]:
                query += " AND title LIKE ?"
                params.append(f"%{kwargs['title']}%")
            if "scope" in kwargs and kwargs["scope"]:
                query += " AND scope LIKE ?"
                params.append(f"%{kwargs['scope']}%")
            if "status" in kwargs and kwargs["status"]:
                if isinstance(kwargs["status"], list):
                    query += " AND status IN ({})".format(
                        ",".join("?" * len(kwargs["status"]))
                    )
                    params.extend(kwargs["status"])
                else:
                    query += " AND status = ?"
                    params.append(kwargs["status"])
            if "support" in kwargs and kwargs["support"]:
                query += " AND scope LIKE ?"
                params.append(f"%{kwargs['support']}%")
            if "tags" in kwargs and kwargs["tags"]:
                query += " AND tags LIKE ?"
                params.append(f"%{kwargs['tags']}%")
            if "description" in kwargs and kwargs["description"]:
                query += " AND description LIKE ?"
                params.append(f"%{kwargs['description']}%")

            nodes = cursor.execute(query, params).fetchall()
            return [NodeBase(**self.node_row_to_dict(node)) for node in nodes]

    def get_random_node(self, node_type: str = None) -> NodeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM nodes"
            params = []
            if node_type:
                query += " WHERE node_type = ?"
                params.append(node_type)
            query += " ORDER BY RANDOM() LIMIT 1"

            node = cursor.execute(query, params).fetchone()
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            return NodeBase(**self.node_row_to_dict(node))

    def get_node(self, node_id: int) -> NodeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            node = cursor.execute(
                "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
            ).fetchone()
            print(node)
            print(self.node_row_to_dict(node))
            if not node:
                raise HTTPException(status_code=404, detail="Node not found")
            return NodeBase(**self.node_row_to_dict(node))

    def find_edges(self, **kwargs) -> list[EdgeBase]:  # TODO: use PartialEdgeBase
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM edges WHERE 1=1"
            params = []
            if "source_id" in kwargs and kwargs["source_id"]:
                query += " AND source = ?"
                params.append(kwargs["source_id"])
            if "target_id" in kwargs and kwargs["target_id"]:
                query += " AND target = ?"
                params.append(kwargs["target_id"])
            if "edge_type" in kwargs and kwargs["edge_type"]:
                query += " AND edge_type = ?"
                params.append(kwargs["edge_type"])

            edges = cursor.execute(query, params).fetchall()
            print("\nedges", edges)
            return [EdgeBase(**self.edge_row_to_dict(edge)) for edge in edges]

    def generate_unique_node_id(self) -> int:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            while True:
                node_id = random.randint(1, 1_000_000_000)
                cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (node_id,))
                if not cursor.fetchone():
                    return node_id

    def create_node(self, node: NodeBase) -> NodeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()

            node_id = self.generate_unique_node_id()  # Generate unique node_id

            field_types = node.get_field_types()
            fields = ["node_id"] + [f for f in field_types.keys()]
            placeholders = ", ".join(["?"] * len(fields))
            serialized_values = [node_id]  # Start with node_id

            for field in fields[1:]:  # Exclude node_id as it's already added
                value = self.serialize_field(
                    field, field_types[field], getattr(node, field)
                )
                serialized_values.append(value)

            insert_sql = f"""
                INSERT INTO nodes ({", ".join(['"'+f+'"' for f in fields])})
                VALUES ({placeholders})
            """
            try:
                cursor.execute(insert_sql, serialized_values)
            except sqlite3.IntegrityError as e:
                raise HTTPException(status_code=400, detail=str(e))

            conn.commit()

            cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()
            if row:
                return NodeBase(**self.node_row_to_dict(row))
            else:
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve the created node."
                )

    def update_node(self, node: PartialNodeBase) -> NodeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            update_fields = []
            params = []

            field_types = node.get_field_types()

            for field, field_type in field_types.items():
                value = getattr(node, field, None)
                if value is not None:
                    serialized_value = self.serialize_field(field, field_type, value)
                    update_fields.append(f'"{field}" = ?')
                    params.append(serialized_value)

            if not update_fields:
                raise HTTPException(
                    status_code=400, detail="No fields provided for update."
                )

            set_clause = ", ".join(update_fields)
            params.append(node.node_id)  # Add node_id for WHERE clause

            update_sql = f"""
                UPDATE nodes
                SET {set_clause}
                WHERE node_id = ?
            """

            try:
                cursor.execute(update_sql, params)
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Node not found.")
                conn.commit()
            except sqlite3.IntegrityError as e:
                self.logger.error(f"IntegrityError while updating node: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node.node_id,))
            row = cursor.fetchone()
            if row:
                return NodeBase(**self.node_row_to_dict(row))
            else:
                raise HTTPException(status_code=500, detail="Failed to update node")

    def delete_node(self, node_id: int) -> None:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Node not found")
            conn.commit()

    def get_edge_list(self) -> list[EdgeBase]:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            edges = cursor.execute("SELECT * FROM edges").fetchall()
            return [EdgeBase(**self.edge_row_to_dict(edge)) for edge in edges]

    def get_edge(self, source_id: int, target_id: int) -> EdgeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            edge = cursor.execute(
                "SELECT * FROM edges WHERE source = ? AND target = ?",
                (source_id, target_id),
            ).fetchone()
            if edge is None:
                raise HTTPException(status_code=404, detail="Edge not found")
            return EdgeBase(**self.edge_row_to_dict(edge))

    def create_edge(self, edge: EdgeBase) -> EdgeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()

            # Verify source and target nodes exist
            cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (edge.source,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Source node not found")

            cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (edge.target,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Target node not found")

            # Handle core fields separately
            core_fields = ["edge_type", "source", "target"]
            core_values = [edge.edge_type.value, edge.source, edge.target]

            # Handle property fields dynamically
            property_field_types = edge.get_field_types()
            property_fields = list(property_field_types.keys())
            property_placeholders = ", ".join(["?"] * len(property_fields))
            serialized_property_values = []

            for field in property_fields:
                value = getattr(edge, field, None)
                serialized_value = self.serialize_field(
                    field, property_field_types[field], value
                )
                serialized_property_values.append(serialized_value)

            # Combine core fields and property fields
            all_fields = core_fields + property_fields
            all_placeholders = ", ".join(["?"] * len(all_fields))
            all_values = core_values + serialized_property_values

            insert_sql = f"""
                INSERT INTO edges ({", ".join(['"'+f+'"' for f in all_fields])})
                VALUES ({all_placeholders})
            """

            try:
                cursor.execute(insert_sql, all_values)
                conn.commit()
            except sqlite3.IntegrityError as e:
                self.logger.error(f"IntegrityError while creating edge: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            cursor.execute(
                "SELECT * FROM edges WHERE edge_type = ? AND source = ? AND target = ?",
                (edge.edge_type.value, edge.source, edge.target),
            )
            new_edge = cursor.fetchone()
            if new_edge:
                return EdgeBase(**self.edge_row_to_dict(new_edge))
            else:
                raise HTTPException(status_code=500, detail="Failed to create edge")

    def update_edge(self, edge: PartialEdgeBase) -> EdgeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            update_fields = []
            params = []

            field_types = edge.get_field_types()

            for field, field_type in field_types.items():
                value = getattr(edge, field, None)
                if value is not None:
                    serialized_value = self.serialize_field(field, field_type, value)
                    update_fields.append(f'"{field}" = ?')
                    params.append(serialized_value)

            if not update_fields:
                raise HTTPException(
                    status_code=400, detail="No fields provided for update."
                )

            set_clause = ", ".join(update_fields)
            # For WHERE clause
            params.extend([edge.edge_type, edge.source, edge.target])

            update_sql = f"""
                UPDATE edges
                SET {set_clause}
                WHERE edge_type = ? AND source = ? AND target = ?
            """

            try:
                cursor.execute(update_sql, params)
                if cursor.rowcount == 0:
                    self.logger.warning(
                        f"Edge not found for update: {edge.edge_type}, {edge.source}, {edge.target}"
                    )
                    raise HTTPException(status_code=404, detail="Edge not found.")
                conn.commit()
            except sqlite3.IntegrityError as e:
                self.logger.error(f"IntegrityError while updating edge: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            cursor.execute(
                "SELECT * FROM edges WHERE edge_type = ? AND source = ? AND target = ?",
                (edge.edge_type, edge.source, edge.target),
            )
            updated_edge = cursor.fetchone()
            if updated_edge:
                return EdgeBase(**self.edge_row_to_dict(updated_edge))
            else:
                raise HTTPException(status_code=500, detail="Failed to update edge")

    def delete_edge(
        self, source_id: int, target_id: int, edge_type: str = None
    ) -> None:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            if edge_type:
                cursor.execute(
                    "DELETE FROM edges WHERE source = ? AND target = ? AND edge_type = ?",
                    (source_id, target_id, edge_type),
                )
            else:
                cursor.execute(
                    "DELETE FROM edges WHERE source = ? AND target = ?",
                    (source_id, target_id),
                )
            if cursor.rowcount == 0:
                detail_msg = (
                    "Edge not found"
                    if edge_type
                    else "No edges found between the specified nodes"
                )
                self.logger.warning(detail_msg)
                raise HTTPException(status_code=404, detail=detail_msg)
            conn.commit()
            self.logger.info(
                f"Deleted edge(s) between source: {source_id}, target: {target_id}, type: {edge_type}"
            )
