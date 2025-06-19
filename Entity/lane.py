# Entity/lane.py

class Lane:
    def __init__(self, id, index, speed, shape, from_node=None, to_node=None, is_internal=False):
        """
        Represents a physical lane in the road network.

        Args:
            id (str): Unique lane ID.
            index (int): Lane index within the edge (starting from 0 on the left).
            speed (float): Speed limit in meters per second.
            shape (str): Shape string from SUMO XML, formatted as "x1,y1 x2,y2 ...".
            from_node (str, optional): ID of the starting node.
            to_node (str, optional): ID of the ending node.
            is_internal (bool): Whether the lane is an internal connector (e.g., at junctions).
        """
        self.id = id                             # Unique lane identifier
        self.index = index                       # Index within the edge (left to right, 0-based)
        self.speed = speed                       # Speed limit in m/s
        self.shape = self._parse_shape(shape)    # Parsed shape as list of (x, y) tuples
        self.from_node = from_node               # Start node ID
        self.to_node = to_node                   # End node ID
        self.is_internal = is_internal           # Flag indicating if this is an internal lane

        # Extension fields for lane connectivity and structure
        self.segment_id = None                   # Associated Segment ID (can be set later)
        self.connected_lanes = []                # List of directly connected lanes (used for connectivity graphs)

    def _parse_shape(self, shape_str):
        """
        Parse a SUMO shape string into a list of (x, y) coordinate tuples.

        Args:
            shape_str (str): Shape string from SUMO, e.g., "100.0,50.0 110.0,55.0".

        Returns:
            List[Tuple[float, float]]: Parsed list of points.
        """
        points = []
        for pair in shape_str.strip().split():
            x, y = map(float, pair.split(','))
            points.append((x, y))
        return points

    def __repr__(self):
        """
        String representation of the Lane object.
        """
        return f"Lane(id={self.id}, from={self.from_node}, to={self.to_node}, internal={self.is_internal})"
