# Controller/vehicle_generator.py
from Entity.vehicle import Vehicle, VehicleStatus
from Entity.slot import Slot
from Entity.vehicle import Vehicle, VehicleStatus, VehicleType
from Entity.route import Route
from Entity.slot import Slot
import random

class VehicleGenerator:
    def __init__(self, route_dict: dict[str, Route], default_vehicle_type: VehicleType):
        """
        Initializes the VehicleGenerator.

        Args:
            route_dict (dict[str, Route]): A dictionary of available routes (route_id -> Route object).
            default_vehicle_type (VehicleType): The default vehicle type to assign to generated vehicles.
        """
        self.global_vehicle_index = 0
        self.generated_vehicles = []
        self.routes = route_dict
        self.default_type = default_vehicle_type

    def select_random_route(self) -> Route:
        """
        Select a random route from available routes.
        (Can be extended to weighted selection in future.)

        Returns:
            Route: A randomly selected Route object.
        """
        return random.choice(list(self.routes.values()))

    def generate_vehicle(self, slot: Slot | None, route: Route) -> Vehicle | None:
        """
        Generate a vehicle and optionally bind it to a slot.

        - If a slot is provided (not None), the vehicle will be assigned to that slot (used for main roads).
        - If no slot is provided, the vehicle will be created without binding (used for on-ramps).

        Args:
            slot (Slot or None): The slot to bind the vehicle to, or None for unbound vehicles.
            route (Route): The route the vehicle will follow.

        Returns:
            Vehicle or None: The created Vehicle object, or None if the slot is already occupied.
        """
        if slot and slot.occupied:
            return None  # Skip creation if the slot is already taken

        veh_id = f"veh_{self.global_vehicle_index}"
        self.global_vehicle_index += 1

        if slot:
            slot.occupy(veh_id)

        vehicle = Vehicle(
            id=veh_id,
            current_slot=slot,
            route=route,
            vehicle_type=self.default_type,
            speed=slot.speed if slot else 0.0,
            position=slot.position_start if slot else 0.0,
            status=VehicleStatus.INITIALIZING
        )

        self.generated_vehicles.append(vehicle)
        return vehicle
