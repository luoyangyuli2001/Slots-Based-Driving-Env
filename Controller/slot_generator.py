import os
import sys
import traci
import math

# === 添加项目根路径，确保 Entity 和 tools 模块可导入 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Entity.slot import Slot
from Sumo.sumo_netxml_parser import parse_netxml
from Tools.utils import generate_temp_cfg

# ==== SUMO 配置 ====
SUMO_BINARY = "sumo-gui"
CFG_FILE = os.path.join("Sim", "temp.sumocfg")
NET_FILE = os.path.join("Sim", "joined_segments.net.xml")


# ==== 工具函数：shape 插值 ====
def interpolate_position_from_shape(shape, target_distance):
    accumulated = 0.0
    for i in range(len(shape) - 1):
        x1, y1 = shape[i]
        x2, y2 = shape[i + 1]
        dx = x2 - x1
        dy = y2 - y1
        segment_length = math.hypot(dx, dy)

        if accumulated + segment_length >= target_distance:
            ratio = (target_distance - accumulated) / segment_length
            interp_x = x1 + ratio * dx
            interp_y = y1 + ratio * dy
            return interp_x, interp_y

        accumulated += segment_length

    return shape[-1]


# ==== 槽位生成器（单条 lane） ====
def generate_slots_for_lane(lane, slot_length=8.0, slot_gap=3.0):
    slots = []
    lane_length = lane.length
    step = slot_length + slot_gap
    num_slots = int(math.floor(lane_length / step))

    shape = traci.lane.getShape(lane.id)

    for i in range(num_slots):
        start_pos = i * step
        slot_id = f"slot_{lane.id}_{i}"
        slot = Slot(
            id=slot_id,
            segment_id=lane.segment_id,
            lane_id=lane.id,
            index=i,
            position_start=start_pos,
            length=slot_length,
            gap_to_previous=slot_gap
        )
        slot.center = interpolate_position_from_shape(shape, slot.center)
        slots.append(slot)

    return slots


# ==== 主程序入口 ====
if __name__ == "__main__":
    print("[INFO] 解析路网...")
    segments = parse_netxml(NET_FILE)

    selected_lane = None
    for seg in segments:
        if seg.segment_type == "standard" and seg.lanes:
            selected_lane = seg.lanes[0]
            selected_lane.segment_id = seg.id
            break

    if not selected_lane:
        print("[ERROR] 未找到有效 lane")
        sys.exit(1)

    print(f"[INFO] 选中 lane: {selected_lane.id}, 长度: {selected_lane.length:.2f} m")

    # === 启动仿真环境 ===
    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])

    # ✅ 关键：初次推进，初始化仿真状态，避免 crash
    traci.simulationStep()

    # === 生成 slot ===
    slots = generate_slots_for_lane(selected_lane)
    print(f"[INFO] 共生成 {len(slots)} 个 slot")

    # === 添加 slot 的 POI 可视化点 ===
    for slot in slots:
        try:
            if slot.center is None:
                continue
            x, y = slot.center
            traci.poi.add(slot.id, x, y, color=(255, 0, 0))  # 红色点
            traci.poi.setParameter(slot.id, "label", slot.id)
            traci.poi.setParameter(slot.id, "imgWidth", "5")
            traci.poi.setParameter(slot.id, "imgHeight", "5")
            traci.poi.setParameter(slot.id, "color", "255,0,0")  # 保底再设置一次

            print(f"[POI] 添加 slot: {slot.id} at ({x:.2f}, {y:.2f})")
        except Exception as e:
            print(f"[ERROR] slot {slot.id} 添加失败: {e}")
            continue

    # === 主仿真循环，观察 POI 效果 ===
    step = 0
    while step < 500:
        traci.simulationStep()
        step += 1

    traci.close()
    print("[INFO] 仿真结束。")
