# Entity/vehicle.py

from enum import Enum

class VehicleStatus(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    TRANSITIONING = "transitioning"
    EXITING = "exiting"

class Vehicle:
    def __init__(self, id, lane, segment, route_entry, route_exit, full_lane,
                 position=0.0, speed=0.0, current_slot=None, status=VehicleStatus.INITIALIZING):
        self.id = id                      # 唯一车辆 ID
        self.lane = lane                  # 当前 Lane
        self.segment = segment            # 当前 Segment
        self.route_entry = route_entry    # 路线起点 ID
        self.route_exit = route_exit      # 路线终点 ID
        self.full_lane = full_lane        # 当前 FullLane
        self.position = position
        self.speed = speed
        self.current_slot = current_slot
        self.status = status

    def __repr__(self):
        return (f"[VEHICLE] {self.id} | pos: {self.position:.2f} | speed: {self.speed:.2f} | "
                f"status: {self.status.value} | lane: {self.lane.id}")
