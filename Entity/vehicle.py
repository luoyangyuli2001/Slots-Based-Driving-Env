# Entity/vehicle.py

from enum import Enum
import math
import traci
from Entity.slot import Slot
from Entity.route import Route

class VehicleStatus(Enum):
    """
    Enum representing the status of a vehicle in the simulation.
    """
    INITIALIZING = 0   # Just created or entering simulation
    IDLE = 1           # Moving normally within its assigned slot
    INTERACTING = 2    # In the middle of an action (lane change, merge, etc.)
    EXITED = 3         # Vehicle has exited the environment

class VehicleType:
    def __init__(self, id: str, accel: float, decel: float, max_speed: float, length: float):
        """
        Represents the physical and control properties of a vehicle type.

        Args:
            id (str): Unique ID for the vehicle type.
            accel (float): Maximum acceleration (m/s^2).
            decel (float): Maximum deceleration (m/s^2).
            max_speed (float): Maximum speed (m/s).
            length (float): Physical length of the vehicle (m).
        """
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
        """
        Represents a vehicle entity in the simulation.

        Args:
            id (str): Unique vehicle ID.
            current_slot (Slot): The slot currently occupied by the vehicle.
            route (Route): Assigned route for the vehicle.
            vehicle_type (VehicleType): Physical characteristics of the vehicle.
            speed (float): Current speed (m/s).
            position (float): Initial position along the route or lane.
            status (VehicleStatus): Current status of the vehicle.
        """
        self.id = id
        self.current_slot = current_slot
        self.route = route
        self.vehicle_type = vehicle_type
        self.speed = speed
        self.position = position
        self.status = status
        self.previous_slot = None  # For tracking slot transitions

    def __repr__(self):
        return f"Vehicle(id={self.id}, route={self.route.id}, slot={self.current_slot.id})"

    def get_current_center_position(self):
        """
        Get the geometric center of the vehicle in real time.
        This is derived from the front bumper position provided by TraCI.

        Returns:
            Tuple[float, float] or None: (x, y) center position if available, else None.
        """
        try:
            x_front, y_front = traci.vehicle.getPosition(self.id)
            heading_deg = traci.vehicle.getAngle(self.id)
            heading_rad = math.radians(heading_deg)
            vehicle_length = traci.vehicle.getLength(self.id)

            x_center = x_front - (vehicle_length / 2.0) * math.cos(heading_rad)
            y_center = y_front - (vehicle_length / 2.0) * math.sin(heading_rad)
            return x_center, y_center
        except Exception:
            # Return None if the vehicle is not yet in the simulation
            return None

    def get_front_position(self):
        """
        Get the front bumper position of the vehicle directly from TraCI.

        Returns:
            Tuple[float, float]: (x, y) position of the vehicle front, or (0.0, 0.0) if unavailable.
        """
        try:
            return traci.vehicle.getPosition(self.id)
        except:
            return (0.0, 0.0)
