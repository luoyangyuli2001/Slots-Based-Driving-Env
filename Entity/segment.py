# Entity/segment.py

class Segment:
    def __init__(self, id, from_node, to_node, segment_type="standard", shape=None):
        """
        Represents a logical road segment, such as a straight section, on-ramp, or off-ramp.

        Args:
            id (str): Unique segment identifier.
            from_node (str): ID of the starting node.
            to_node (str): ID of the ending node.
            segment_type (str, optional): Type of the segment. Defaults to "standard".
                Other options include "on_ramp" and "off_ramp".
            shape (List[Tuple[float, float]], optional): Optional shape points for visualization or geometry.
        """
        self.id = id                              # Unique segment ID
        self.from_node = from_node                # Start node ID
        self.to_node = to_node                    # End node ID
        self.segment_type = segment_type          # Segment type: "standard", "on_ramp", or "off_ramp"
        self.shape = shape or []                  # Optional geometric shape of the segment
        self.lanes = []                           # List of Lane instances belonging to this segment

    def add_lane(self, lane):
        """
        Add a lane to the segment.

        Args:
            lane (Lane): A Lane instance to be added to the segment.
        """
        self.lanes.append(lane)

    def __repr__(self):
        """
        String representation of the Segment object.
        """
        return f"Segment(id={self.id}, type={self.segment_type}, lanes={len(self.lanes)}, from={self.from_node}, to={self.to_node})"
