# Test/test_slot_generator.py

import os
import sys
import traci
import time

# Add project root to sys.path for import
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
    print("[TEST] Initialize road network and generate slots (static visualization only)")
    parser = NetXMLParser(NET_FILE)
    full_lanes = parser.build_full_lanes()

    # Generate temporary SUMO config file
    generate_temp_cfg()

    # Start SUMO simulation
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    # Generate static slots on all full lanes
    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)

    print("[TEST] Visualizing all slots in the SUMO GUI")
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
                    print(f"[WARN] Failed to add slot {slot.id}: {e}")

    traci.close()
