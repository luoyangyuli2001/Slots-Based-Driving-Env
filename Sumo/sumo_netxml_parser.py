# Sumo/sumo_netxml_parser.py

import os
import sys
import xml.etree.ElementTree as ET

# 添加项目根目录到 sys.path 便于进行测试
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Entity.segment import Segment
from Entity.lane import Lane
from Entity.fulllane import FullLane


def classify_segment(edge_id):
    """
    基于 edge_id 的命名判断 segment 类型
    1. on-ramp
    2. off-ramp
    3. standard --> straight
    """
    if "ramp" in edge_id.lower():
        return "on_ramp"
    elif "exit" in edge_id.lower():
        return "off_ramp"
    else:
        return "standard"

def is_internal_edge(edge_element):
    """
    判断是否是 SUMO 自动生成的 internal edge
    """
    edge_id = edge_element.get("id", "")
    function = edge_element.get("function", "")
    return edge_id.startswith(":") or function == "internal"

def parse_netxml(netxml_path):
    """
    解析 .net.xml 文件，构建 Segment 和 Lane 实体对象，并基于 index 设置 next_lane
    """
    tree = ET.parse(netxml_path)
    root = tree.getroot()
    segments = []
    lane_dict = {}

    # === Step 1: 解析所有 edge 与 lane，构建 Segment 与 Lane 实体 ===
    for edge in root.findall("edge"):
        if is_internal_edge(edge):
            continue

        edge_id = edge.get("id")
        from_node = edge.get("from")
        to_node = edge.get("to")
        shape_points = []
        shape = edge.get("shape")
        if shape:
            shape_points = [tuple(map(float, p.split(','))) for p in shape.strip().split()]

        # 构建 Lane 实体列表
        lanes = []
        for lane_elem in edge.findall("lane"):
            lane = Lane(
                id=lane_elem.get("id"),
                index=int(lane_elem.get("index")),
                speed=float(lane_elem.get("speed")),
                length=float(lane_elem.get("length")),
                shape=[tuple(map(float, p.split(','))) for p in lane_elem.get("shape", "").strip().split()]
            )
            lanes.append(lane)
            lane_dict[lane.id] = lane

        # 构建 Segment 对象
        segment = Segment(
            id=edge_id,
            from_node=from_node,
            to_node=to_node,
            segment_type=classify_segment(edge_id),
            shape=shape_points
        )

        for lane in lanes:
            lane.segment_id = segment.id
            segment.add_lane(lane)

        segments.append(segment)

    # === Step 2: 构建 lane.next_lane 引用（右舵左行 lane 对齐）===
    # ✅ 使用 index 基于 segment 顺序构建 next_lane 显式连接关系
    segment_dict = {seg.id: seg for seg in segments}

    for i in range(len(segments) - 1):
        curr_seg = segments[i]
        next_seg = segments[i + 1]

        if curr_seg.segment_type != "standard" or next_seg.segment_type != "standard":
            continue

        n1 = len(curr_seg.lanes)
        n2 = len(next_seg.lanes)

        for curr_lane in curr_seg.lanes:
            i1 = curr_lane.index
            offset = n2 - n1
            i2 = i1 + offset

            if 0 <= i2 < n2:
                for next_lane in next_seg.lanes:
                    if next_lane.index == i2:
                        curr_lane.next_lane = next_lane
                        break

    # === Step 3: 标记 entry_lane / end_lane，并建立 entry_ref ===
    # 构建所有被引用为 next_lane 的 lane_id 集合, 用于下一步标记 entry lane 
    # 没有被其他lane标记为next_lane的就是entry lane
    next_lane_ids = set()
    for seg in segments:
        for lane in seg.lanes:
            if lane.next_lane:
                next_lane_ids.add(lane.next_lane.id)

    entry_lanes = []
    # 标记 entry lane（仅主干道参与）
    for seg in segments:
        if seg.segment_type != "standard":
            continue
        for lane in seg.lanes:
            if lane.id not in next_lane_ids:
                lane.is_entry = True
                entry_lanes.append(lane)

    # 从每个 entry lane 出发, 寻找对应的 end lane. 并分别标记entry与end
    for entry in entry_lanes:
        current = entry
        visited = set()
        while current and current.id not in visited:
            visited.add(current.id)
            if not current.next_lane:
                current.is_end = True
                current.entry_ref = entry
                break
            current = current.next_lane

    # === Step 4: 构建 FullLane 实体列表 ===
    full_lanes = []
    full_lane_index = 0

    for lane in lane_dict.values():
        if getattr(lane, "is_entry", False):
            full_lane = FullLane(id=f"full_{full_lane_index}")
            full_lane_index += 1

            current = lane
            while current:
                full_lane.add_lane(current)
                current.full_lane = full_lane
                if getattr(current, "is_end", False):
                    break
                current = current.next_lane

            full_lanes.append(full_lane)

    return segments, full_lanes

# 测试入口
if __name__ == "__main__":
    net_path = "Sim/joined_segments.net.xml"
    segments, full_lanes = parse_netxml(net_path)

    print(f"共解析出 {len(segments)} 个 Segment:")
    for seg in segments:
        print(f"[SEGMENT] {seg.id} ({seg.segment_type})")
        for lane in seg.lanes:
            next_id = lane.next_lane.id if lane.next_lane else "None"
            print(f"   [LANE] {lane.id} -> next_lane: {next_id}")
            print(f"   [LANE] {lane.id} is entry? {lane.is_entry}")
            print(f"   [LANE] {lane.id} is end? {lane.is_end}")
            print(f"   [LANE] {lane.id} is entry -> {lane.entry_ref}")

    print(f"\n共构建 {len(full_lanes)} 条 FullLane:")
    for fl in full_lanes:
        print(fl)
