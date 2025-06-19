# Entity/slot.py

class Slot:
    def __init__(self,
                 id,
                 segment_id,
                 lane,
                 index,
                 position_start,
                 speed,
                 length=8.0,
                 gap_to_previous=3.0,
                 vehicle_id=None,
                 heading=0.0,
                 full_lane=None):
        """
        Represents a virtual traffic slot (space reservation) on a lane for vehicle control.

        Args:
            id (str): Unique identifier of the slot.
            segment_id (str): ID of the segment the slot belongs to.
            lane (Lane): The Lane instance where this slot resides.
            index (int): Global index of the slot for unique ordering.
            position_start (float): Start position (arc length) along the lane.
            speed (float): Target speed of the slot (in m/s).
            length (float, optional): Length of the slot. Defaults to 8.0 meters.
            gap_to_previous (float, optional): Gap to the previous slot. Defaults to 3.0 meters.
            vehicle_id (str, optional): ID of the vehicle occupying the slot. Defaults to None.
            heading (float, optional): Heading angle in degrees (relative to SUMO coordinates).
            full_lane (FullLane, optional): Reference to the full logical lane this slot belongs to.
        """
        self.id = id                              # Unique slot ID
        self.segment_id = segment_id              # Segment the slot is part of
        self.lane = lane                          # Lane object this slot is located on
        self.index = index                        # Global slot index
        self.position_start = position_start      # Start position (arc length) on the lane
        self.length = length                      # Physical length of the slot
        self.gap_to_previous = gap_to_previous    # Gap from the previous slot
        self.speed = speed                        # Target speed of the slot (m/s)
        self.position_end = self.position_start + self.length  # End position along the lane
        self.center = (self.position_start + self.position_end) / 2  # Approximate center (scalar, arc-length)
        self.heading = heading                    # Heading angle in degrees (relative to SUMO)
        self.occupied = False                     # Whether the slot is currently occupied by a vehicle
        self.vehicle_id = vehicle_id              # ID of the occupying vehicle, if any
        self.full_lane = full_lane                # Reference to the full logical lane
        self.busy = False                         # Whether the slot is currently involved in an action

    def occupy(self, vehicle_id):
        """
        Mark the slot as occupied by the given vehicle.

        Args:
            vehicle_id (str): ID of the occupying vehicle.
        """
        self.occupied = True
        self.vehicle_id = vehicle_id

    def release(self):
        """
        Release the slot (mark as unoccupied).
        """
        self.occupied = False
        self.vehicle_id = None

    def __repr__(self):
        """
        String representation of the Slot object.
        """
        return (f"Slot(id={self.id}, lane={self.lane.id}, index={self.index}, "
                f"range=({self.position_start:.2f}-{self.position_end:.2f}), "
                f"center={self.center:.2f}, heading={self.heading:.2f}, "
                f"occupied={self.occupied}, vehicle={self.vehicle_id})")
