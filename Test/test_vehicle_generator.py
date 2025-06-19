# Test/test_vehicle_generator.py

import os
import sys
import time
import random
import traci
import math
from collections import defaultdict

# Set up path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import NetXMLParser
from Sumo.sumo_routexml_parser import RouteXMLParser
from Tools.utils import generate_temp_cfg
from Controller.slot_generator import SlotGenerator
from Controller.slot_controller import SlotController
from Controller.vehicle_generator import VehicleGenerator
from Controller.merge_controller import MergeController
from Controller.vehicle_controller import VehicleController

# SUMO configuration paths
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/test.net.xml"
ROUTE_FILE = "Sim/test.rou.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    print("[TEST] Launch SUMO and generate Slots and Vehicles")
    generate_temp_cfg()

    # Load FullLane and Route
    net_parser = NetXMLParser(NET_FILE)
    full_lanes = net_parser.build_full_lanes()
    lane_dict = net_parser.lane_dict

    route_parser = RouteXMLParser(ROUTE_FILE)
    routes = route_parser.get_routes()
    route_groups = route_parser.get_route_groups()
    default_vtype = route_parser.get_default_vehicle_type()

    # Start SUMO
    traci.start([SUMO_BINARY, "-c", CFG_FILE])
    traci.simulationStep()

    # Initialize Slot system
    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)
    slot_controller = SlotController(slot_generator, full_lanes)

    # Initialize Vehicle system
    vehicle_generator = VehicleGenerator(routes, default_vtype)

    rendered_slots = set()
    rendered_vehicles = set()
    vehicle_list = []

    # Initial slot visualization
    for fl in full_lanes:
        for slot in fl.slots:
            if slot.center:
                x, y = slot.center
                try:
                    traci.poi.add(slot.id, x, y, color=(255, 0, 0), layer=5)
                    traci.poi.setParameter(slot.id, "label", slot.id)
                    rendered_slots.add(slot.id)
                except:
                    pass

    # Initialize vehicle controller
    vehicle_controller = VehicleController(vehicle_list, route_groups)

    # Initialize merge controller
    ramp_to_fulllane_map = {
        "on_ramp1": "e2_0",
        "-on_ramp1": "-e6_0"
    }

    merge_controller = MergeController(full_lanes, ramp_to_fulllane_map, safety_gap=5.0)

    print("[TEST] Start dynamically adding vehicles and updating slots")
    for step in range(5000):
        traci.simulationStep()

        # Advance slot and get removed ones
        removed = slot_controller.step()

        # === Vehicle controller updates vehicle status in real time ===
        vehicle_controller.step()

        # === Merge controller checks for merges in real time ===
        merge_controller.step(vehicle_list)

        # Update existing slot positions or add new slots
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

        # Remove and regenerate slots
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
                rendered_slots.discard(old_slot.id)
            except:
                pass

        # Add a vehicle every 30 steps (demo only)
        if step % 30 == 0:
            selected_route = vehicle_generator.select_random_route()
            entry_edge = selected_route.edges[0]

            candidate_lanes = [lane for lane in lane_dict.values() if lane.id.startswith(entry_edge + "_")]
            if not candidate_lanes:
                print(f"[WARN] No valid lane found on edge {entry_edge}")
                continue
            
            selected_lane = random.choice(candidate_lanes)

            # Check if it's a ramp
            is_ramp = "ramp" in selected_lane.id.lower()

            vehicle = None
            if is_ramp:
                vehicle = vehicle_generator.generate_vehicle(slot=None, route=selected_route)
            else:
                # Find FullLane and assign slot
                target_fl = None
                for fl in full_lanes:
                    if fl.start_lane_id == selected_lane.id:
                        target_fl = fl
                        break

                if not target_fl or not target_fl.slots:
                    print(f"[INFO] No suitable FullLane or no available slot found: {selected_lane.id}")
                    continue

                slot = target_fl.slots[0]
                if getattr(slot, "occupied", False):
                    print(f"[INFO] Slot {slot.id} is already occupied, skipping")
                    continue

                vehicle = vehicle_generator.generate_vehicle(slot=slot, route=selected_route)

            if vehicle and vehicle.id not in rendered_vehicles:
                try:
                    if vehicle.current_slot:
                        slot = vehicle.current_slot
                        traci.vehicle.add(
                            vehID=vehicle.id,
                            routeID=vehicle.route.id,
                            typeID=vehicle.vehicle_type.id,
                            departPos=str(slot.position_start),
                            departSpeed=str(slot.speed),
                            departLane=slot.lane.id.split("_")[-1]
                        )
                        # Disable lane changing
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)

                        # Disable automatic acceleration
                        # Default (all checks enabled) -> [0 0 1 1 1 1 1] -> Speed mode = 31
                        # Most checks disabled (legacy) -> [0 0 0 0 0 0 0] -> Speed mode = 0
                        # All checks disabled -> [1 1 0 0 0 0 0] -> Speed mode = 96
                        # Disable right-of-way check -> [0 1 1 0 1 1 1] -> Speed mode = 55
                        # Run red light [0 0 0 0 1 1 1] = 7 (also requires setSpeed or slowDown)
                        # Force run red light even if someone is in intersection [0 1 0 0 1 1 1] = 39 (also requires setSpeed or slowDown)

                        traci.vehicle.setSpeedMode(vehicle.id, 0)
                        traci.vehicle.setSpeed(vehicle.id, vehicle.speed)

                        # === Use slot.heading to accurately place the vehicle ===
                        vehicle_length = vehicle.vehicle_type.length
                        heading_rad = math.radians(slot.heading)
                        x_center, y_center = slot.center
                        x_front = x_center + (vehicle_length / 2.0) * math.cos(heading_rad)
                        y_front = y_center + (vehicle_length / 2.0) * math.sin(heading_rad)

                        edge_id = slot.lane.id.rsplit("_", 1)[0]
                        lane_index = int(slot.lane.id.rsplit("_", 1)[-1])
                        traci.vehicle.moveToXY(
                            vehicle.id, edgeID=edge_id, laneIndex=lane_index,
                            x=x_front, y=y_front, angle=slot.heading, keepRoute=1
                        )
                    else:
                        traci.vehicle.add(
                            vehID=vehicle.id,
                            routeID=vehicle.route.id,
                            typeID=vehicle.vehicle_type.id,
                            departLane=selected_lane.id.split("_")[-1],
                            departSpeed="0",
                            departPos="0"
                        )
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)
                        traci.vehicle.setSpeedMode(vehicle.id, 0)

                    rendered_vehicles.add(vehicle.id)
                    vehicle_list.append(vehicle)

                    print(f"[ADD VEH] {vehicle.id} added successfully, route: {selected_route.id}")
                except Exception as e:
                    print(f"[WARN] Failed to add {vehicle.id}: {e}")

    traci.close()
    print("[TEST] Test completed")
