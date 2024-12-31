import sqlite3
from fastapi import HTTPException

from models import NodeBase, EdgeBase, Subnet
from .base import DatabaseInterface


class SQLiteDB(DatabaseInterface):
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                node_id INTEGER PRIMARY KEY,
                node_type TEXT,
                title TEXT,
                scope TEXT,
                status TEXT,
                description TEXT,
                tags TEXT,
                "references" TEXT
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                edge_id INTEGER PRIMARY KEY,
                edge_type TEXT,
                source INTEGER,
                target INTEGER,
                cprob REAL,
                "references" TEXT,
                description TEXT,
                FOREIGN KEY(source) REFERENCES nodes(node_id),
                FOREIGN KEY(target) REFERENCES nodes(node_id)
            )
        """
        )
        self.conn.commit()

    def get_whole_network(self) -> Subnet:
        nodes = self.cursor.execute("SELECT * FROM nodes").fetchall()
        edges = self.cursor.execute("SELECT * FROM edges").fetchall()
        return Subnet(nodes=nodes, edges=edges)

    def get_network_summary(self) -> dict:
        node_count = self.cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = self.cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        return {"nodes": node_count, "edges": edge_count}

    def reset_whole_network(self) -> None:
        self.cursor.execute("DELETE FROM nodes")
        self.cursor.execute("DELETE FROM edges")
        self.conn.commit()

    def update_subnet(self, subnet: Subnet) -> Subnet:
        mapping = {}
        nodes_out = []
        edges_out = []
        for node in subnet.nodes:
            if node.node_id is not None:
                self.cursor.execute(
                    "SELECT 1 FROM nodes WHERE node_id = ?", (node.node_id,)
                )
                if self.cursor.fetchone():
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
            self.cursor.execute(
                "SELECT 1 FROM edges WHERE source = ? AND target = ? AND edge_type = ?",
                (edge.source, edge.target, edge.edge_type),
            )
            if self.cursor.fetchone():
                edge_out = self.update_edge(edge)
            else:
                edge_out = self.create_edge(edge)
            edges_out.append(edge_out)

        return Subnet(nodes=nodes_out, edges=edges_out)

    def get_induced_subnet(self, node_id: int, levels: int) -> Subnet:
        nodes = self.cursor.execute(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchall()
        if not nodes:
            return Subnet(nodes=[], edges=[])

        edges = self.cursor.execute(
            "SELECT * FROM edges WHERE source = ? OR target = ?", (node_id, node_id)
        ).fetchall()
        return Subnet(nodes=nodes, edges=edges)

    def search_nodes(self, **kwargs) -> list[NodeBase]:
        query = "SELECT * FROM nodes WHERE 1=1"
        params = []
        if "node_type" in kwargs and kwargs["node_type"]:
            query += " AND node_type = ?"
            params.append(kwargs["node_type"])
        if "title" in kwargs and kwargs["title"]:
            query += " AND title LIKE ?"
            params.append(f"%{kwargs['title']}%")
        if "scope" in kwargs and kwargs["scope"]:
            query += " AND scope LIKE ?"
            params.append(f"%{kwargs['scope']}%")
        if "status" in kwargs and kwargs["status"]:
            query += " AND status = ?"
            params.append(kwargs["status"])
        if "tags" in kwargs and kwargs["tags"]:
            query += " AND tags LIKE ?"
            params.append(f"%{kwargs['tags']}%")
        if "description" in kwargs and kwargs["description"]:
            query += " AND description LIKE ?"
            params.append(f"%{kwargs['description']}%")

        nodes = self.cursor.execute(query, params).fetchall()
        return [NodeBase(**row_to_dict(self.cursor, node)) for node in nodes]

    def get_random_node(self, node_type: str = None) -> NodeBase:
        query = "SELECT * FROM nodes"
        params = []
        if node_type:
            query += " WHERE node_type = ?"
            params.append(node_type)
        query += " ORDER BY RANDOM() LIMIT 1"

        node = self.cursor.execute(query, params).fetchone()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return NodeBase(**row_to_dict(self.cursor, node))

    def get_node(self, node_id: int) -> NodeBase:
        node = self.cursor.execute(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return NodeBase(**row_to_dict(self.cursor, node))

    def find_edges(self, **kwargs) -> list[EdgeBase]:
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

        edges = self.cursor.execute(query, params).fetchall()
        return [EdgeBase(**row_to_dict(self.cursor, edge)) for edge in edges]

    def create_node(self, node: NodeBase) -> NodeBase:
        self.cursor.execute(
            """
            INSERT INTO nodes (node_type, title, scope, status, description, tags, "references")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                node.node_type,
                node.title,
                node.scope,
                node.status,
                node.description,
                ";".join(node.tags),
                ";".join(node.references),
            ),
        )
        self.conn.commit()
        node_id = self.cursor.lastrowid
        node.node_id = node_id
        return NodeBase(**node.model_dump())

    def delete_node(self, node_id: int) -> None:
        self.cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
        self.conn.commit()

    def update_node(self, node: NodeBase) -> NodeBase:
        self.cursor.execute(
            """
            UPDATE nodes
            SET node_type = ?, title = ?, scope = ?, status = ?, description = ?, tags = ?, "references" = ?
            WHERE node_id = ?
        """,
            (
                node.node_type,
                node.title,
                node.scope,
                node.status,
                node.description,
                ";".join(node.tags),
                ";".join(node.references),
                node.node_id,
            ),
        )
        self.conn.commit()
        return node

    def get_edge_list(self) -> list[EdgeBase]:
        edges = self.cursor.execute("SELECT * FROM edges").fetchall()
        return [EdgeBase(**row_to_dict(self.cursor, edge)) for edge in edges]

    def get_edge(self, source_id: int, target_id: int) -> EdgeBase:
        edge = self.cursor.execute(
            "SELECT * FROM edges WHERE source = ? AND target = ?",
            (source_id, target_id),
        ).fetchone()
        return EdgeBase(**row_to_dict(self.cursor, edge))

    def create_edge(self, edge: EdgeBase) -> EdgeBase:
        self.cursor.execute(
            """
            INSERT INTO edges (edge_type, source, target, cprob, "references", description)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                edge.edge_type,
                edge.source,
                edge.target,
                edge.cprob,
                ";".join(edge.references),
                edge.description,
            ),
        )
        self.conn.commit()
        edge_id = self.cursor.lastrowid
        return EdgeBase(edge_id=edge_id, **edge.model_dump())

    def delete_edge(
        self, source_id: int, target_id: int, edge_type: str = None
    ) -> None:
        if edge_type:
            self.cursor.execute(
                "DELETE FROM edges WHERE source = ? AND target = ? AND edge_type = ?",
                (source_id, target_id, edge_type),
            )
        else:
            self.cursor.execute(
                "DELETE FROM edges WHERE source = ? AND target = ?",
                (source_id, target_id),
            )
        self.conn.commit()

    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        self.cursor.execute(
            """
            UPDATE edges
            SET edge_type = ?, source = ?, target = ?, cprob = ?, "references" = ?, description = ?
            WHERE edge_id = ?
        """,
            (
                edge.edge_type,
                edge.source,
                edge.target,
                edge.cprob,
                ";".join(edge.references),
                edge.description,
                edge.edge_id,
            ),
        )
        self.conn.commit()
        return edge


def row_to_dict(cursor, row):
    return dict(zip([column[0] for column in cursor.description], row))
