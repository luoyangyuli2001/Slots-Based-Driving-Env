# Test/test_slot_controller_generator.py

import os
import sys
import traci
import time

# Add project root to sys.path for testing
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

    # Generate temporary SUMO configuration file
    generate_temp_cfg()

    # Start SUMO simulation
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    # Generate initial slots on all full lanes
    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)

    # Initialize SlotController to simulate slot flow
    slot_controller = SlotController(slot_generator, full_lanes)

    # Track rendered slots for visual updates
    rendered_slots = set()

    # Render initial slots
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
                    print(f"[WARN] Failed to add initial slot {slot.id}: {e}")

    print("[TEST] Starting dynamic slot flow simulation...")
    for step in range(1000):
        traci.simulationStep()

        # Advance all slots and retrieve removed ones
        removed = slot_controller.step()

        # Update slot positions or add new slots if needed
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
                            print(f"[WARN] Failed to add new slot {slot.id}: {e}")

        # Remove old slots from visualization
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
                rendered_slots.discard(old_slot.id)
            except:
                pass

    traci.close()
    print("[TEST] Slot flow simulation ended.")
