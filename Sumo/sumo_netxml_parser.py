import xml.etree.ElementTree as ET
from collections import defaultdict
from Entity.lane import Lane
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

        for edge in root.findall("edge"):
            for lane_elem in edge.findall("lane"):
                lane_id = lane_elem.get("id")
                index = int(lane_elem.get("index"))
                speed = float(lane_elem.get("speed"))
                shape = lane_elem.get("shape")
                lane = Lane(id=lane_id, index=index, speed=speed, shape=shape)
                self.lane_dict[lane_id] = lane

    def build_full_lanes(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

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

        full_lanes = []
        lane_to_fulllane = {}

        start_lanes = [lane_id for lane_id in lane_graph if lane_id not in incoming]
        for start_lane in start_lanes:
            visited = set()
            current = start_lane
            full_lane = FullLane(start_lane_id=start_lane)

            while current and current not in visited:
                visited.add(current)
                if current in self.lane_dict:
                    full_lane.add_lane(self.lane_dict[current])
                    lane_to_fulllane[current] = full_lane
                next_list = lane_graph.get(current, [])
                current = next_list[0] if next_list else None

            if full_lane.lanes:
                full_lanes.append(full_lane)

        # 设置邻接 FullLane（带方向标记）
        for full_lane in full_lanes:
            for lane in full_lane.lanes:
                lane_id = lane.id
                edge_base = "_".join(lane_id.split("_")[:-1])
                lane_index = int(lane_id.split("_")[-1])

                for delta in [-1, 1]:
                    neighbor_index = lane_index + delta
                    neighbor_lane_id = f"{edge_base}_{neighbor_index}"

                    if neighbor_lane_id in lane_to_fulllane:
                        neighbor_full_lane = lane_to_fulllane[neighbor_lane_id]

                        # ✅ 右舵左行环境下编号越小越靠左：
                        # -1 表示左侧 +1 表示右侧
                        # delta > 0 表示右边 → direction = +1
                        # delta < 0 表示左边 → direction = -1
                        direction = +1 if delta > 0 else -1

                        start_x = lane.shape[0][0]
                        end_x = lane.shape[-1][0]
                        full_lane.add_neighbor_full_lane(start_x, end_x, neighbor_full_lane, direction)

        # 合并邻接 FullLane 的区间
        for full_lane in full_lanes:
            self._merge_neighbor_full_lanes(full_lane)

        return full_lanes

    def _merge_neighbor_full_lanes(self, full_lane):
        """将 FullLane 中重复邻居的多个区间合并，保留方向信息"""
        from collections import defaultdict

        merged = defaultdict(lambda: defaultdict(list))  # neighbor_full_lane -> direction -> [(start_x, end_x)]

        for start_x, end_x, neighbor, direction in full_lane.neighbor_full_lanes:
            start, end = min(start_x, end_x), max(start_x, end_x)
            merged[neighbor][direction].append((start, end))

        full_lane.neighbor_full_lanes = []
        for neighbor, dir_intervals in merged.items():
            for direction, intervals in dir_intervals.items():
                intervals.sort()
                merged_ranges = []
                current_start, current_end = intervals[0]
                for start, end in intervals[1:]:
                    if start <= current_end + 1e-3:
                        current_end = max(current_end, end)
                    else:
                        merged_ranges.append((current_start, current_end))
                        current_start, current_end = start, end
                merged_ranges.append((current_start, current_end))
                for start, end in merged_ranges:
                    full_lane.neighbor_full_lanes.append((start, end, neighbor, direction))
