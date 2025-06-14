import logging
from abc import ABC, ABCMeta, abstractmethod
from functools import wraps

from backend.models import (
    NodeBase,
    EdgeBase,
    SubnetBase,
    User,
    UserRead,
    UserCreate,
    NodeId,
    RatingEvent,
    RatingType,
    LikertScale,
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


class RatingHistoryRelationalInterface(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def log_rating(self, rating: RatingEvent) -> RatingEvent:
        """
        Log a rating for a given entity and user.
        """
        pass

    def get_node_rating(
        self, node_id: NodeId, rating_type: RatingType, username: str
    ) -> RatingEvent | None:
        """
        Retrieve the rating of a given node by a given user.
        """
        pass

    def get_node_ratings(
        self, node_id: int, rating_type: RatingType
    ) -> list[RatingEvent]:
        """
        Retrieve the most recent rating per user for a given node using PostgreSQL's DISTINCT ON.
        """
        pass

    def get_edge_rating(
        self,
        source_id: NodeId,
        target_id: NodeId,
        rating_type: RatingType,
        username: str,
    ) -> RatingEvent | None:
        """
        Retrieve the rating of a given edge by a given user.
        """
        pass

    def get_edge_ratings(
        self, source_id: int, target_id: int, rating_type: RatingType
    ) -> list[RatingEvent]:
        """
        Retrieve the most recent rating per user for a given edge using PostgreSQL's DISTINCT ON.
        """
        pass

    def get_node_median_rating(
        self, node_id: NodeId, rating_type: RatingType
    ) -> LikertScale | None:
        """
        Retrieve the latest median rating (LikertScale) of a given node.
        """
        pass

    def get_edge_median_rating(
        self, source_id: NodeId, target_id: NodeId, rating_type: RatingType
    ) -> LikertScale | None:
        """
        Retrieve the median rating (LikertScale) of a given edge.
        """
        pass

    def get_nodes_median_ratings(
        self, node_ids: list[NodeId], rating_type: RatingType
    ) -> dict[NodeId, LikertScale | None]:
        """
        Retrieve the latest median ratings for multiple nodes.
        Returns a mapping: { node_id: median_rating }.
        If a node has no ratings, median_rating is None.
        """
        pass


class GraphDatabaseInterface(ABC, metaclass=LogMeta):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_whole_network(self) -> SubnetBase:
        pass

    @abstractmethod
    def get_network_summary(self) -> dict:
        pass

    @abstractmethod
    def reset_whole_network(self) -> None:
        pass

    @abstractmethod
    def update_subnet(self, subnet: SubnetBase) -> SubnetBase:
        pass

    @abstractmethod
    def get_induced_subnet(self, node_id: NodeId, levels: NodeId) -> SubnetBase:
        pass

    @abstractmethod
    def search_nodes(self, **kwargs) -> list[NodeBase]:
        pass

    @abstractmethod
    def get_random_node(self, node_type: str = None) -> NodeBase:
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
        self, source_id: NodeId, target_id: NodeId, edge_type: str = None
    ) -> None:
        pass

    @abstractmethod
    def update_edge(self, edge: EdgeBase) -> EdgeBase:
        pass


class GraphHistoryRelationalInterface(GraphDatabaseInterface):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # some inherited methods have added parameter username
    @abstractmethod
    def reset_whole_network(self, username: str) -> None:
        pass

    @abstractmethod
    def update_subnet(self, subnet: SubnetBase, username: str) -> SubnetBase:
        pass

    @abstractmethod
    def create_node(self, node: NodeBase, username: str) -> NodeBase:
        pass

    @abstractmethod
    def delete_node(self, node_id: NodeId, username: str) -> None:
        pass

    @abstractmethod
    def update_node(self, node: NodeBase, username: str) -> NodeBase:
        pass

    @abstractmethod
    def create_edge(self, edge: EdgeBase, username: str) -> EdgeBase:
        pass

    @abstractmethod
    def delete_edge(
        self, source_id: NodeId, target_id: NodeId, edge_type: str, username: str
    ) -> None:
        pass

    @abstractmethod
    def update_edge(self, edge: EdgeBase, username: str) -> EdgeBase:
        pass

    # history-specific methods
    @abstractmethod
    def log_event(self, event) -> object:
        """
        Log an event (create, update, delete) for an entity.
        """
        pass

    @abstractmethod
    def get_node_history(self, node_id: NodeId) -> list:
        """
        Retrieve all events for a given entity.
        """
        pass

    @abstractmethod
    def get_edge_history(self, source_id: NodeId, target_id: NodeId) -> list:
        """
        Retrieve all events for a given entity.
        """
        pass

    @abstractmethod
    def revert_to_event(self, event_id: NodeId) -> None:
        """
        Revert the entity state to a given event.
        """
        pass
