# Test/test_slot_controller_generator.py

import os
import sys
import traci
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import NetXMLParser
from Tools.utils import generate_temp_cfg
from Controller.slot_generator import SlotGenerator
from Controller.slot_controller import SlotController

# SUMO Configuration
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/test.net.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    parser = NetXMLParser(NET_FILE)
    full_lanes = parser.build_full_lanes()
    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)
    # === 初始化 SlotController 控制 slot 流动 ===
    slot_controller = SlotController(slot_generator, full_lanes)

    # 初始化渲染已添加的 slot 集合
    rendered_slots = set()

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
                    rendered_slots.add(slot.id)
                except Exception as e:
                    print(f"[WARN] 初始 slot {slot.id} 添加失败：{e}")

    print("[TEST] 启动 slot 动态流动模拟...")
    for step in range(1000):
        traci.simulationStep()

        # 推进 slot 并获取移除项
        removed = slot_controller.step()

        # 更新现有 slot 坐标或添加新 slot
        for fl in full_lanes:
            for slot in fl.slots:
                if slot.center:
                    if slot.id in rendered_slots:
                        try:
                            traci.poi.setPosition(slot.id, *slot.center)
                        except:
                            pass
                    else:
                        try:
                            traci.poi.add(slot.id, *slot.center, color=(255, 0, 0), layer=5)
                            traci.poi.setParameter(slot.id, "label", slot.id)
                            traci.poi.setParameter(slot.id, "imgWidth", "5")
                            traci.poi.setParameter(slot.id, "imgHeight", "5")
                            rendered_slots.add(slot.id)
                        except Exception as e:
                            print(f"[WARN] 新 slot {slot.id} 添加失败: {e}")

        # 移除并补充 slot
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
                rendered_slots.discard(old_slot.id)
            except:
                pass

    traci.close()
    print("[TEST] 流动测试结束。")