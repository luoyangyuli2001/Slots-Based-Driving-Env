# Entity/full_lane.py

import math

class FullLane:
    def __init__(self, start_lane_id):
        """
        Represents a complete logical lane composed of multiple connected physical lanes.

        Args:
            start_lane_id (str): The ID of the first lane in the sequence.
        """
        self.start_lane_id = start_lane_id
        self.lanes = []  # Ordered list of lanes following the driving direction
        self.full_shape = []  # Combined shape points (geometry) of the full lane
        self.neighbor_full_lanes = []  # List of neighboring FullLanes: (start_x, end_x, neighbor, direction)

    def add_lane(self, lane):
        """
        Add a lane to the full lane in order and update the overall shape.

        Args:
            lane (Lane): A Lane instance to append to the FullLane.
        """
        if not self.lanes:
            self.full_shape.extend(lane.shape)
        else:
            last_point = self.full_shape[-1]
            if lane.shape and lane.shape[0] == last_point:
                self.full_shape.extend(lane.shape[1:])  # Avoid duplicate point
            else:
                self.full_shape.extend(lane.shape)
        self.lanes.append(lane)

    def add_neighbor_full_lane(self, start_x, end_x, neighbor_full_lane, direction):
        """
        Register an adjacent FullLane for potential lane-changing.

        Args:
            start_x (float): Start x-coordinate of the overlapping area.
            end_x (float): End x-coordinate of the overlapping area.
            neighbor_full_lane (FullLane): The adjacent FullLane instance.
            direction (int): -1 for left neighbor, 1 for right neighbor.
        """
        self.neighbor_full_lanes.append((start_x, end_x, neighbor_full_lane, direction))

    def find_neighbor_slot_by_position(self, position_x, position_y):
        """
        Find the closest available slot in neighboring FullLanes at a given position.

        Args:
            position_x (float): X coordinate of the current vehicle/slot.
            position_y (float): Y coordinate of the current vehicle/slot.

        Returns:
            Slot or None: The best candidate slot if found, otherwise None.
        """
        best_slot = None
        min_dist = float('inf')

        for start_x, end_x, neighbor_lane in self.neighbor_full_lanes:
            if not (start_x <= position_x <= end_x):
                continue
            if not hasattr(neighbor_lane, "slots"):
                continue
            for slot in neighbor_lane.slots:
                if slot.occupied:
                    continue
                sx, sy = slot.center
                dist = math.hypot(sx - position_x, sy - position_y)
                if dist < min_dist:
                    min_dist = dist
                    best_slot = slot

        return best_slot

    def get_total_length(self):
        """
        Compute the total geometric arc length of this FullLane.

        Returns:
            float: Total length in meters.
        """
        length = 0
        for i in range(1, len(self.full_shape)):
            x1, y1 = self.full_shape[i - 1]
            x2, y2 = self.full_shape[i]
            length += math.hypot(x2 - x1, y2 - y1)
        return length

    def __repr__(self):
        """
        String representation of the FullLane object.
        """
        return f"FullLane(start={self.start_lane_id}, lanes={[lane.id for lane in self.lanes]})"
        # Optional detailed representation:
        # return f"FullLane(start={self.start_lane_id}, lanes={[lane.id for lane in self.lanes]}, shape={self.full_shape})"
