# Test/test_slot_controller_generator.py

import os
import sys
import traci
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import parse_netxml
from Tools.utils import generate_temp_cfg
from Controller.slot_generator import generate_slots_for_all_full_lanes, generate_single_slot_on_full_lane
from Controller.slot_controller import SlotController

# SUMO Configuration
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/joined_segments.net.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    print("[TEST] 初始化路网并生成 slot")
    segments, full_lanes = parse_netxml(NET_FILE)

    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    generate_slots_for_all_full_lanes(full_lanes)
    slot_controller = SlotController(full_lanes)

    # 可视化初始 slot
    for fl in full_lanes:
        for slot in fl.slots:
            if slot.center:
                x, y = slot.center
                try:
                    traci.poi.add(slot.id, x, y, color=(255, 0, 0), layer=5)
                    traci.poi.setParameter(slot.id, "label", slot.id)
                    traci.poi.setParameter(slot.id, "imgWidth", "5")
                    traci.poi.setParameter(slot.id, "imgHeight", "5")
                except Exception as e:
                    print(f"[WARN] 初始 slot {slot.id} 添加失败：{e}")

    print("[TEST] 启动 slot 动态流动模拟...")
    for step in range(1000):
        traci.simulationStep()

        # 推进一帧，并获取被移除的 slot
        removed = slot_controller.step()
        slot_controller.update_center_by_shape()

        # 刷新 slot 位置
        for fl in full_lanes:
            for slot in fl.slots:
                if slot.center:
                    try:
                        traci.poi.setPosition(slot.id, *slot.center)
                    except:
                        pass

        # slot 再生：从末尾移除，从起点补充
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
            except:
                pass

            new_slot = generate_single_slot_on_full_lane(full_lane)
            full_lane.slots.append(new_slot)

            if new_slot.center:
                try:
                    traci.poi.add(new_slot.id, *new_slot.center, color=(255, 0, 0), layer=5)
                    traci.poi.setParameter(new_slot.id, "label", new_slot.id)
                    traci.poi.setParameter(new_slot.id, "imgWidth", "5")
                    traci.poi.setParameter(new_slot.id, "imgHeight", "5")
                except Exception as e:
                    print(f"[WARN] 新 slot {new_slot.id} 添加失败：{e}")

    traci.close()
    print("[TEST] 流动测试结束。")