# Sumo/sumo_routexml_parser.py

import xml.etree.ElementTree as ET
from Entity.route import Route
from Entity.vehicle import VehicleType
from collections import defaultdict

class RouteXMLParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.routes: dict[str, Route] = {}
        self.vehicle_types: dict[str, VehicleType] = {}
        self.route_groups: dict[str, list[str]] = {}

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

        # 解析路线并构建 route_groups
        temp_groups = defaultdict(list)
        for route in root.findall("route"):
            route_id = route.get("id")
            edges = route.get("edges", "").split()
            self.routes[route_id] = Route(route_id, edges)

            if not route_id.startswith("route_"):
                continue

            parts = route_id.split("_")
            if len(parts) < 3:
                continue  # 忽略格式不正确的

            _, entry, exit = parts[:3]
            is_reverse = parts[-1] == "r"

            # 组名构造，如：main_forward, onramp1_reverse
            direction = "reverse" if is_reverse else "forward"
            group_name = f"{entry}_{direction}"
            temp_groups[group_name].append((exit, route_id))

        # 对每组 route 根据终点优先级排序：offramp 优先，main 最后
        def sort_key(item):
            exit_name, _ = item
            if exit_name.startswith("offramp"):
                return int(exit_name.replace("offramp", ""))
            elif exit_name == "main":
                return 9999  # main 排最后
            else:
                return 10000  # 其他未知出口排最后

        self.route_groups = {
            group: [route_id for _, route_id in sorted(items, key=sort_key)]
            for group, items in temp_groups.items()
        }

    def get_routes(self) -> dict[str, Route]:
        return self.routes

    def get_vehicle_types(self) -> dict[str, VehicleType]:
        return self.vehicle_types

    def get_default_vehicle_type(self) -> VehicleType:
        return next(iter(self.vehicle_types.values())) if self.vehicle_types else None

    def get_route_groups(self) -> dict[str, list[str]]:
        return self.route_groups
