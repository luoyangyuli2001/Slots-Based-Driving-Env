# Entity/route.py

class Route:
    def __init__(self, id, edges):
        """
        Represents a vehicle route composed of a sequence of edge IDs.

        Args:
            id (str): Unique identifier for the route.
            edges (List[str]): Ordered list of edge IDs that form the route path.
        """
        self.id = id              # Unique route identifier
        self.edges = edges        # List of edge IDs in travel order

    def __repr__(self):
        """
        String representation of the Route object.
        """
        return f"Route(id={self.id}, edges={self.edges})"
