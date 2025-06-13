# Controller/vehicle_generator.py

from Entity.vehicle import Vehicle, VehicleStatus
from Entity.slot import Slot
from Entity.fulllane import FullLane

import random
from Entity.vehicle import Vehicle, VehicleStatus, VehicleType
from Entity.route import Route
from Entity.slot import Slot

class VehicleGenerator:
    def __init__(self, route_dict: dict[str, Route], default_vehicle_type: VehicleType):
        self.global_vehicle_index = 0
        self.generated_vehicles = []
        self.routes = route_dict
        self.default_type = default_vehicle_type

    def select_random_route(self) -> Route:
        """默认随机选一条路线（可后续支持按比例）"""
        return random.choice(list(self.routes.values()))

    def generate_vehicle(self, slot: Slot | None, route: Route) -> Vehicle | None:
        """
        生成车辆：如果 slot 不为 None，则绑定 slot（用于主干道）；
        否则生成未绑定 slot 的车辆（用于 on-ramp）
        """
        if slot and slot.occupied:
            return None

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
