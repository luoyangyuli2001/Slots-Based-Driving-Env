# Sumo/sumo_routexml_parser.py

import xml.etree.ElementTree as ET
from Entity.route import Route
from Entity.vehicle import VehicleType

class RouteXMLParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.routes: dict[str, Route] = {}
        self.vehicle_types: dict[str, VehicleType] = {}

        self._parse()

    def _parse(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # 解析车辆类型
        for vtype in root.findall("vType"):
            id = vtype.get("id")
            accel = float(vtype.get("accel", 2.6))
            decel = float(vtype.get("decel", 4.5))
            max_speed = float(vtype.get("maxSpeed", 27.78))
            length = float(vtype.get("length", 5.0))
            self.vehicle_types[id] = VehicleType(id, accel, decel, max_speed, length)

        # 解析路线
        for route in root.findall("route"):
            id = route.get("id")
            edges = route.get("edges", "").split()
            self.routes[id] = Route(id, edges)

    def get_routes(self) -> dict[str, Route]:
        return self.routes

    def get_vehicle_types(self) -> dict[str, VehicleType]:
        return self.vehicle_types

    def get_default_vehicle_type(self) -> VehicleType:
        return next(iter(self.vehicle_types.values())) if self.vehicle_types else None