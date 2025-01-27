import logging
from abc import ABC, ABCMeta, abstractmethod
from functools import wraps

from models import NodeBase, EdgeBase, Subnet, User


logging.basicConfig(level=logging.DEBUG)


def log_method(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.logger.debug(
            f"Entering: {func.__name__} with args: {args} kwargs: {kwargs}"
        )
        try:
            result = func(self, *args, **kwargs)
            self.logger.debug(f"Exiting: {func.__name__} with result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Exception in {func.__name__}: {e}")
            raise

    return wrapper


class LogMeta(ABCMeta):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.items():
            if callable(attr_value) and not attr_name.startswith("__"):
                attrs[attr_name] = log_method(attr_value)
        return super().__new__(cls, name, bases, attrs)


class UserDatabaseInterface(ABC):
    @abstractmethod
    def create_user(self, user: User):
        pass

    @abstractmethod
    def get_user(self, username: str) -> User:
        pass


class GraphDatabaseInterface(ABC, metaclass=LogMeta):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

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
