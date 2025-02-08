import logging
from abc import ABC, ABCMeta, abstractmethod
from functools import wraps

from models import (
    NodeBase,
    EdgeBase,
    Subnet,
    User,
    UserRead,
    UserCreate,
    NodeId,
    NodeType,
    EdgeType,
)


logging.basicConfig(level=logging.INFO)


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
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def create_user(self, user: UserCreate) -> UserRead:
        pass

    @abstractmethod
    def get_user(self, username: str) -> User | None:
        pass

    @abstractmethod
    def update_user(self, user: User) -> UserRead:
        pass

    @abstractmethod
    def update_preferences(self, username: str, new_prefs: dict) -> UserRead:
        pass

    @abstractmethod
    def reset_user_table(self):
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
    def get_induced_subnet(self, node_id: NodeId, levels: NodeId) -> Subnet:
        pass

    @abstractmethod
    def search_nodes(self, **kwargs) -> list[NodeBase]:
        pass

    @abstractmethod
    def get_random_node(self, node_type: NodeType = None) -> NodeBase:
        pass

    @abstractmethod
    def get_node(self, node_id: NodeId) -> NodeBase:
        pass

    @abstractmethod
    def create_node(self, node: NodeBase) -> NodeBase:
        pass

    @abstractmethod
    def delete_node(self, node_id: NodeId) -> None:
        pass

    @abstractmethod
    def update_node(self, node: NodeBase) -> NodeBase:
        pass

    @abstractmethod
    def get_edge_list(self) -> list[EdgeBase]:
        pass

    @abstractmethod
    def get_edge(self, source_id: NodeId, target_id: NodeId) -> EdgeBase:
        pass

    @abstractmethod
    def find_edges(self, **kwargs) -> list[EdgeBase]:
        pass

    @abstractmethod
    def create_edge(self, edge: EdgeBase) -> EdgeBase:
        pass

    @abstractmethod
    def delete_edge(
        self, source_id: NodeId, target_id: NodeId, edge_type: EdgeType = None
    ) -> None:
        pass

    @abstractmethod
    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        pass


class GraphHistoryDatabaseInterface(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def log_event(self, event) -> object:
        """
        Log an event (create, update, delete) for an entity.
        """
        pass

    @abstractmethod
    def get_node_history(self, node_id: int) -> list:
        """
        Retrieve all events for a given entity.
        """
        pass

    @abstractmethod
    def get_edge_history(self, source_id: int, target_id: int) -> list:
        """
        Retrieve all events for a given entity.
        """
        pass

    @abstractmethod
    def revert_to_event(self, event_id: int) -> None:
        """
        Revert the entity state to a given event.
        """
        pass
