# Sumo/sumo_netxml_parser.py

import xml.etree.ElementTree as ET
from collections import defaultdict
from Entity.lane import Lane
from Entity.segment import Segment
from Entity.fulllane import FullLane


class NetXMLParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lane_dict = {}
        self.connections = []
        self._parse_all_edges()

    def _parse_all_edges(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # 1. 构建所有 Lane 实体
        for edge in root.findall("edge"):
            for lane_elem in edge.findall("lane"):
                lane_id = lane_elem.get("id")
                index = int(lane_elem.get("index"))
                speed = float(lane_elem.get("speed"))
                shape = lane_elem.get("shape")
                lane = Lane(id=lane_id, index=index, speed=speed, shape=shape)
                self.lane_dict[lane_id] = lane

    def build_full_lanes(self) -> list[FullLane]:
        """
        从 net.xml 文件中构建所有主干道 FullLane 实体
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # 1. 构建 lane-to-lane 连接图
        lane_graph = defaultdict(list)
        incoming = defaultdict(set)

        for conn in root.findall("connection"):
            from_edge = conn.get("from")
            to_edge = conn.get("to")
            via = conn.get("via")
            from_lane = conn.get("fromLane")
            to_lane = conn.get("toLane")

            if not (from_edge and to_edge and via and from_lane is not None and to_lane is not None):
                continue
            if "ramp" in from_edge.lower() or "ramp" in to_edge.lower():
                continue

            from_lane_id = f"{from_edge}_{from_lane}"
            via_lane_id = via
            to_lane_id = f"{to_edge}_{to_lane}"

            if from_lane_id in self.lane_dict and via_lane_id in self.lane_dict and to_lane_id in self.lane_dict:
                lane_graph[from_lane_id].append(via_lane_id)
                lane_graph[via_lane_id].append(to_lane_id)
                incoming[via_lane_id].add(from_lane_id)
                incoming[to_lane_id].add(via_lane_id)

        # 3. 找起点 lane（无前驱）
        start_lanes = [lane_id for lane_id in lane_graph if lane_id not in incoming]

        # 4. 构建 FullLane
        full_lanes = []
        for start_lane in start_lanes:
            visited = set()
            current = start_lane
            full_lane = FullLane(start_lane_id=start_lane)
            while current and current not in visited:
                visited.add(current)
                if current in self.lane_dict:
                    full_lane.add_lane(self.lane_dict[current])
                next_list = lane_graph.get(current, [])
                current = next_list[0] if next_list else None

            if full_lane.lanes:
                full_lanes.append(full_lane)

        return full_lanes