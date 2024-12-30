from abc import ABC, abstractmethod
from models import NodeBase, EdgeBase, Subnet


class DatabaseInterface(ABC):
    @abstractmethod
    def get_whole_network(self) -> Subnet:
        pass

    @abstractmethod
    def get_network_summary(self) -> dict:
        pass

    @abstractmethod
    def reset_whole_network(self) -> None:
        pass

    @abstractmethod
    def update_subnet(self, subnet: Subnet) -> Subnet:
        pass

    @abstractmethod
    def get_induced_subnet(self, node_id: int, levels: int) -> Subnet:
        pass

    @abstractmethod
    def search_nodes(self, **kwargs) -> list[NodeBase]:
        pass

    @abstractmethod
    def get_random_node(self, node_type: str = None) -> NodeBase:
        pass

    @abstractmethod
    def get_node(self, node_id: int) -> NodeBase:
        pass

    @abstractmethod
    def create_node(self, node: NodeBase) -> NodeBase:
        pass

    @abstractmethod
    def delete_node(self, node_id: int) -> None:
        pass

    @abstractmethod
    def update_node(self, node: NodeBase) -> NodeBase:
        pass

    @abstractmethod
    def get_edge_list(self) -> list[EdgeBase]:
        pass

    @abstractmethod
    def get_edge(self, source_id: int, target_id: int) -> EdgeBase:
        pass

    @abstractmethod
    def find_edges(self, **kwargs) -> list[EdgeBase]:
        pass

    @abstractmethod
    def create_edge(self, edge: EdgeBase) -> EdgeBase:
        pass

    @abstractmethod
    def delete_edge(
        self, source_id: int, target_id: int, edge_type: str = None
    ) -> None:
        pass

    @abstractmethod
    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        pass
