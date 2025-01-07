import random

import sqlite3
from fastapi import HTTPException

from models import NodeBase, EdgeBase, Subnet, PartialNodeBase
from .base import DatabaseInterface


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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id INTEGER PRIMARY KEY,
                    node_type TEXT,
                    title TEXT,
                    scope TEXT,
                    status TEXT,
                    support TEXT,
                    description TEXT,
                    tags TEXT,
                    "references" TEXT
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    edge_type TEXT,
                    source INTEGER,
                    target INTEGER,
                    cprob REAL,
                    "references" TEXT,
                    description TEXT,
                    FOREIGN KEY(source) REFERENCES nodes(node_id),
                    FOREIGN KEY(target) REFERENCES nodes(node_id),
                    UNIQUE(source, target, edge_type)
                )
                """
            )
            conn.commit()
            self.node_description = cursor.execute(
                "SELECT * FROM nodes LIMIT 1"
            ).description
            self.edge_description = cursor.execute(
                "SELECT * FROM edges LIMIT 1"
            ).description

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
                        node_out.id_from_ui = node.node_id
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

    def find_edges(self, **kwargs) -> list[EdgeBase]:
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
            cursor.execute(
                """
                INSERT INTO nodes (node_id, node_type, title, scope, status, support, description, tags, "references")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    node.node_type,
                    node.title,
                    node.scope,
                    node.status,
                    node.support,
                    node.description,
                    ";".join(node.tags) if node.tags else "",
                    ";".join(node.references) if node.references else "",
                ),
            )
            conn.commit()
            cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
            row = cursor.fetchone()
            if row:
                return NodeBase(**self.node_row_to_dict(row))
            else:
                raise HTTPException(status_code=500, detail="Failed to create node")

    def update_node(self, node: PartialNodeBase) -> NodeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            fields = []
            params = []
            if node.node_type is not None:
                fields.append("node_type = ?")
                params.append(node.node_type)
            if node.title is not None:
                fields.append("title = ?")
                params.append(node.title)
            if node.scope is not None:
                fields.append("scope = ?")
                params.append(node.scope)
            if node.status is not None:
                fields.append("status = ?")
                params.append(node.status)
            if node.support is not None:
                fields.append("support = ?")
                params.append(node.support)
            if node.description is not None:
                fields.append("description = ?")
                params.append(node.description)
            if node.tags is not None:
                fields.append("tags = ?")
                params.append(";".join(node.tags))
            if node.references is not None:
                fields.append('"references" = ?')
                params.append(";".join(node.references))
            set_clause = ", ".join(fields)
            cursor.execute(
                f"""
                UPDATE nodes
                SET {set_clause}
                WHERE node_id = ?
                """,
                (*params, node.node_id),
            )
            conn.commit()
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
            cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (edge.source,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Source node not found")
            cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (edge.target,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Target node not found")
            cursor.execute(
                """
                INSERT OR IGNORE INTO edges (edge_type, source, target, cprob, "references", description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.edge_type,
                    edge.source,
                    edge.target,
                    edge.cprob,
                    ";".join(edge.references) if edge.references else "",
                    edge.description if edge.description else "",
                ),
            )
            conn.commit()
            cursor.execute(
                "SELECT * FROM edges WHERE edge_type = ? AND source = ? AND target = ?",
                (edge.edge_type, edge.source, edge.target),
            )
            new_edge = cursor.fetchone()
            if new_edge:
                return EdgeBase(**self.edge_row_to_dict(new_edge))
            else:
                raise HTTPException(status_code=500, detail="Failed to create edge")

    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        with sqlite3.connect(self.db_path, check_same_thread=False, uri=True) as conn:
            cursor = conn.cursor()
            fields = []
            params = []
            if edge.cprob is not None:
                fields.append("cprob = ?")
                params.append(edge.cprob)
            if edge.references is not None:
                fields.append('"references" = ?')
                params.append(";".join(edge.references))
            if edge.description is not None:
                fields.append("description = ?")
                params.append(edge.description)
            set_clause = ", ".join(fields)
            cursor.execute(
                f"""
                UPDATE edges
                SET {set_clause}
                WHERE edge_type = ? AND source = ? AND target = ?
                """,
                (*params, edge.edge_type, edge.source, edge.target),
            )
            conn.commit()
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
            conn.commit()

    def node_row_to_dict(self, row):
        if row is None:
            return {}
        d = dict(zip([column[0] for column in self.node_description], row))
        d["node_id"] = d.get("node_id")
        d["node_type"] = d.get("node_type")
        d["title"] = d.get("title")
        d["scope"] = d.get("scope")
        d["status"] = d.get("status")
        d["support"] = d.get("support")
        d["description"] = d.get("description")
        if "tags" in d:
            d["tags"] = d["tags"].split(";") if d["tags"] else []
        if "references" in d:
            d["references"] = d["references"].split(";") if d["references"] else []
        return d

    def edge_row_to_dict(self, row):
        if row is None:
            return {}
        d = dict(zip([column[0] for column in self.edge_description], row))
        d["edge_type"] = d.get("edge_type")
        d["source"] = d.get("source")
        d["target"] = d.get("target")
        d["cprob"] = d.get("cprob")
        d["description"] = d.get("description")
        if "references" in d:
            d["references"] = d["references"].split(";") if d["references"] else []
        return d
