# Entity/Segment.py

class Segment:
    def __init__(self, id, from_node, to_node, segment_type="standard", shape=None):
        self.id = id
        self.from_node = from_node
        self.to_node = to_node
        self.segment_type = segment_type  # e.g., "standard", "on_ramp", "off_ramp"
        self.shape = shape or []
        self.lanes = []  # List of Lane objects

    def add_lane(self, lane):
        self.lanes.append(lane)

    def __repr__(self):
        return f"Segment(id={self.id}, type={self.segment_type}, lanes={len(self.lanes)}, from={self.from_node}, to={self.to_node})"
