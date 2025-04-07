import os
import sys
import traci
import math

# === 设置路径 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Entity.slot import Slot
from Sumo.sumo_netxml_parser import parse_netxml
from Tools.utils import generate_temp_cfg

SUMO_BINARY = "sumo-gui"
CFG_FILE = os.path.join("Sim", "temp.sumocfg")
NET_FILE = os.path.join("Sim", "joined_segments.net.xml")

global_index = 0

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

def generate_single_slot_on_lane(lane, slot_length=8.0, slot_gap=3.0):
    global global_index
    slot_id = f"slot_{global_index}"
    global_index += 1
    return Slot(
        id=slot_id,
        lane=lane,
        index=-1,
        position_start=0.0,
        length=slot_length,
        gap_to_previous=slot_gap,
        segment_id=lane.segment_id,
        speed=lane.speed
    )


def generate_slots_for_lane(lane, slot_length=8.0, slot_gap=3.0):
    global global_index
    slots = []
    lane_length = lane.length
    step = slot_length + slot_gap
    num_slots = int(math.floor(lane_length / step))
    shape = traci.lane.getShape(lane.id)

    for i in range(num_slots):
        global_index += 1
        start_pos = i * step
        slot_id = f"slot_{global_index}"

        slot = Slot(
            id=slot_id,
            segment_id=lane.segment_id,
            lane=lane,
            index=global_index,
            position_start=start_pos,
            length=slot_length,
            gap_to_previous=slot_gap,
            speed=lane.speed
        )
        slot.center = interpolate_position_from_shape(shape, slot.center)
        slots.append(slot)

    return slots


def generate_slots_for_all_segments(segments, slot_length=8.0, slot_gap=3.0):
    all_slots = []

    for segment in segments:
        if segment.segment_type != "standard":
            continue

        segment_slots = []
        for lane in segment.lanes:
            lane.segment_id = segment.id
            lane_slots = generate_slots_for_lane(
                lane,
                slot_length=slot_length,
                slot_gap=slot_gap
            )
            segment_slots.extend(lane_slots)


        segment.slots = segment_slots
        all_slots.extend(segment_slots)

    return all_slots


if __name__ == "__main__":
    print("[INFO] 解析路网...")
    segments = parse_netxml(NET_FILE)

    print(f"[INFO] 路网包含 {len(segments)} 个 segment")

    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    all_slots = generate_slots_for_all_segments(segments)
    print(f"[INFO] 共生成 {len(all_slots)} 个 slot（仅在主干道）")

    for slot in all_slots:
        try:
            if slot.center is None:
                continue
            x, y = slot.center
            traci.poi.add(slot.id, x, y, color=(255, 0, 0))
            traci.poi.setParameter(slot.id, "label", slot.id)
            traci.poi.setParameter(slot.id, "imgWidth", "5")
            traci.poi.setParameter(slot.id, "imgHeight", "5")
        except Exception as e:
            print(f"[ERROR] slot {slot.id} 添加失败: {e}")

    step = 0
    while step < 500:
        traci.simulationStep()
        step += 1

    traci.close()
    print("[INFO] 仿真结束。")
