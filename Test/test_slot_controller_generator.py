# Test/test_slot_controller_generator.py

import os
import sys
import time
import traci

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import parse_netxml
from Tools.utils import generate_temp_cfg
from Controller.slot_generator import generate_slots_for_all_segments
from Controller.slot_controller import SlotController

SUMO_BINARY = "sumo-gui"
NET_FILE = os.path.join("Sim", "joined_segments.net.xml")
CFG_FILE = os.path.join("Sim", "temp.sumocfg")

if __name__ == "__main__":
    print("[TEST] 初始化路网并生成 slot")
    segments = parse_netxml(NET_FILE)

    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    all_slots = generate_slots_for_all_segments(segments)
    slot_controller = SlotController(all_slots, time_step=0.1)

    lane_shape_lookup = {
        lane.id: traci.lane.getShape(lane.id)
        for seg in segments for lane in seg.lanes
    }
    slot_controller.update_center_by_lane_shape(lane_shape_lookup)

    # 初始化 POI
    existing_slot_ids = set()
    for slot in all_slots:
        if slot.center:
            x, y = slot.center
            traci.poi.add(slot.id, x, y, color=(255, 0, 0))
            traci.poi.setParameter(slot.id, "label", slot.id)
            traci.poi.setParameter(slot.id, "imgWidth", "5")
            traci.poi.setParameter(slot.id, "imgHeight", "5")
            existing_slot_ids.add(slot.id)
    
    print("[TEST] 启动 slot 动态流动模拟...")
    for step in range(1000):
        traci.simulationStep()

        # Step slots
        slot_controller.step()
        slot_controller.update_center_by_lane_shape(lane_shape_lookup)

        for slot in slot_controller.slots:
            if not slot.center:
                continue
            x, y = slot.center
            if slot.id in existing_slot_ids:
                try:
                    traci.poi.setPosition(slot.id, x, y)
                except:
                    pass
            else:
                try:
                    traci.poi.add(slot.id, x, y, color=(255, 0, 0))
                    traci.poi.setParameter(slot.id, "label", slot.id)
                    traci.poi.setParameter(slot.id, "imgWidth", "5")
                    traci.poi.setParameter(slot.id, "imgHeight", "5")
                    existing_slot_ids.add(slot.id)
                except:
                    pass

        # ✅ 清理已消失的 POI
        current_ids = set(slot.id for slot in slot_controller.slots)
        removed_ids = existing_slot_ids - current_ids
        for rid in removed_ids:
            try:
                traci.poi.remove(rid)
            except:
                pass
        existing_slot_ids = current_ids

    traci.close()
    print("[TEST] 流动测试结束。")
