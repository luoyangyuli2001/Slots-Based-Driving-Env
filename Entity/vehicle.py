# Entity/vehicle.py

from enum import Enum
from Entity.slot import Slot
from Entity.route import Route

class VehicleStatus(Enum):
    INITIALIZING = 0
    IDLE = 1
    INTERACTING = 2
    EXITED = 3

class VehicleType:
    def __init__(self, id: str, accel: float, decel: float, max_speed: float, length: float):
        self.id = id
        self.accel = accel
        self.decel = decel
        self.max_speed = max_speed
        self.length = length

    def __repr__(self):
        return f"VehicleType(id={self.id}, max_speed={self.max_speed}, length={self.length})"

class Vehicle:
    def __init__(self,
                 id: str,
                 current_slot: Slot,
                 route: Route,
                 vehicle_type: VehicleType,
                 speed: float,
                 position: float,
                 status: VehicleStatus = VehicleStatus.INITIALIZING):
        self.id = id
        self.current_slot = current_slot
        self.route = route
        self.vehicle_type = vehicle_type
        self.speed = speed
        self.position = position
        self.status = status

    def __repr__(self):
        return f"Vehicle(id={self.id}, route={self.route.id}, slot={self.current_slot.id})"
