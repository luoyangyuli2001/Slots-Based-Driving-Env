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
    解析 .net.xml 文件，构建 Segment 和 Lane 实体对象
    """
    tree = ET.parse(netxml_path)
    root = tree.getroot()
    segments = []

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

        # 构建 Segment 对象
        segment = Segment(
            id=edge_id,
            from_node=from_node,
            to_node=to_node,
            segment_type=classify_segment(edge_id),
            shape=shape_points
        )

        for lane in lanes:
            segment.add_lane(lane)

        segments.append(segment)

    return segments

# 测试入口
if __name__ == "__main__":
    net_path = "Sim/joined_segments.net.xml"
    segments = parse_netxml(net_path)

    print(f"共解析出 {len(segments)} 个 Segment:")
    for seg in segments:
        print(seg)
        for lane in seg.lanes:
            print("   ", lane)
