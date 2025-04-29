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

# SUMO Configuration
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/test.net.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    print("[TEST] 初始化路网并生成 slot（无流动，仅可视化）")
    parser = NetXMLParser(NET_FILE)
    full_lanes = parser.build_full_lanes()
    generate_temp_cfg()
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)

    print("[TEST] 在 GUI 中可视化所有 slot")
    rendered_slots = set()

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
                    print(f"[WARN] slot {slot.id} 添加失败：{e}")

    traci.close()
