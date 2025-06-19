# Sumo/sumo_routexml_parser.py

import xml.etree.ElementTree as ET
from Entity.route import Route
from Entity.vehicle import VehicleType
from collections import defaultdict

class RouteXMLParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.routes: dict[str, Route] = {}                 # Route ID → Route object
        self.vehicle_types: dict[str, VehicleType] = {}    # VehicleType ID → VehicleType object
        self.route_groups: dict[str, list[str]] = {}       # Group name → list of route IDs

        self._parse()

    def _parse(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # Parse vehicle types defined in <vType> tags
        for vtype in root.findall("vType"):
            id = vtype.get("id")
            accel = float(vtype.get("accel", 2.6))
            decel = float(vtype.get("decel", 4.5))
            max_speed = float(vtype.get("maxSpeed", 27.78))
            length = float(vtype.get("length", 5.0))
            self.vehicle_types[id] = VehicleType(id, accel, decel, max_speed, length)

        # Parse <route> definitions and group them by entry and direction
        temp_groups = defaultdict(list)
        for route in root.findall("route"):
            route_id = route.get("id")
            edges = route.get("edges", "").split()
            self.routes[route_id] = Route(route_id, edges)

            if not route_id.startswith("route_"):
                continue

            parts = route_id.split("_")
            if len(parts) < 3:
                continue  # Skip malformed route IDs

            _, entry, exit = parts[:3]
            is_reverse = parts[-1] == "r"

            # Construct group name: e.g., main_forward, onramp1_reverse
            direction = "reverse" if is_reverse else "forward"
            group_name = f"{entry}_{direction}"
            temp_groups[group_name].append((exit, route_id))

        # Sort routes within each group by exit priority:
        # offramp routes first, main routes last
        def sort_key(item):
            exit_name, _ = item
            if exit_name.startswith("offramp"):
                return int(exit_name.replace("offramp", ""))
            elif exit_name == "main":
                return 9999
            else:
                return 10000  # Other unknown exits at the end

        self.route_groups = {
            group: [route_id for _, route_id in sorted(items, key=sort_key)]
            for group, items in temp_groups.items()
        }

    def get_routes(self) -> dict[str, Route]:
        return self.routes

    def get_vehicle_types(self) -> dict[str, VehicleType]:
        return self.vehicle_types

    def get_default_vehicle_type(self) -> VehicleType:
        # Return the first vehicle type as default (if any)
        return next(iter(self.vehicle_types.values())) if self.vehicle_types else None

    def get_route_groups(self) -> dict[str, list[str]]:
        return self.route_groups
