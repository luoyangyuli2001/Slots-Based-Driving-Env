# Test/test_vehicle_controller.py

import os
import sys
import time
import random
import traci
import math
from collections import defaultdict

# Set path
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

# SUMO configuration
SUMO_BINARY = "sumo-gui"
NET_FILE = "Sim/test.net.xml"
ROUTE_FILE = "Sim/test.rou.xml"
CFG_FILE = "Sim/temp.sumocfg"

if __name__ == "__main__":
    print("[TEST] Starting SUMO and generating slots and vehicles")
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

    # Initialize slot system
    slot_generator = SlotGenerator()
    slot_generator.generate_slots_for_all_full_lanes(full_lanes)
    slot_controller = SlotController(slot_generator, full_lanes)

    # Initialize vehicle system
    vehicle_generator = VehicleGenerator(routes, default_vtype)

    rendered_slots = set()
    rendered_vehicles = set()
    vehicle_list = []

    # Visualize initial slots
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

    print("[TEST] Start adding vehicles dynamically and updating slots")
    for step in range(5000):
        traci.simulationStep()

        # Advance slot controller and collect removed slots
        removed = slot_controller.step()

        # Update all vehicle states
        vehicle_controller.step()

        # Merge controller checks merging conditions
        merge_controller.step(vehicle_list)

        # Update existing slot positions or add new ones
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

        # Remove disappeared slots
        for old_slot, full_lane in removed:
            try:
                traci.poi.remove(old_slot.id)
                rendered_slots.discard(old_slot.id)
            except:
                pass

        # Add a new vehicle at step 30 (for demonstration)
        if step == 30:
            selected_route = vehicle_generator.select_random_route()
            entry_edge = selected_route.edges[0]
            candidate_lanes = [lane for lane in lane_dict.values() if lane.id.startswith(entry_edge + "_")]
            if not candidate_lanes:
                print(f"[WARN] No available lane on edge {entry_edge}")
                continue

            selected_lane = random.choice(candidate_lanes)
            is_ramp = "ramp" in selected_lane.id.lower()

            vehicle = None
            if is_ramp:
                vehicle = vehicle_generator.generate_vehicle(slot=None, route=selected_route)
            else:
                # Find corresponding FullLane
                target_fl = None
                for fl in full_lanes:
                    if fl.start_lane_id == selected_lane.id:
                        target_fl = fl
                        break

                if not target_fl or not target_fl.slots:
                    print(f"[INFO] No valid FullLane or slot for {selected_lane.id}")
                    continue

                slot = target_fl.slots[0]
                if getattr(slot, "occupied", False):
                    print(f"[INFO] Slot {slot.id} already occupied, skipping")
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
                        # Disable lane change and auto acceleration
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)
                        traci.vehicle.setSpeedMode(vehicle.id, 0)
                        traci.vehicle.setSpeed(vehicle.id, vehicle.speed)

                        # Use slot heading for precise placement
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

                    print(f"[ADD VEH] {vehicle.id} added on route {selected_route.id}")
                except Exception as e:
                    print(f"[WARN] Failed to add {vehicle.id}: {e}")

        # # === Execute forward slot movement (action 1) at step 200 ===
        # if step == 200 and target_vehicle and target_vehicle.current_slot:
        #     print("[ACTION] Execute slot forward action 1")
        #     vehicle_controller.execute_slot_action(target_vehicle.current_slot, 1)

        # # === Execute backward slot movement (action 2) at step 300 ===
        # if step == 300 and target_vehicle and target_vehicle.current_slot:
        #     print("[ACTION] Execute slot backward action 2")
        #     vehicle_controller.execute_slot_action(target_vehicle.current_slot, 2)


        # === Execute lane change right at step 200 ===
        if step == 200 and len(vehicle_list) >= 1:
            target_vehicle = vehicle_list[0]
            if target_vehicle.current_slot:
                print("[ACTION] Execute lane change right (action 4)")
                vehicle_controller.execute_slot_action(target_vehicle.current_slot, 4)

        # === Execute lane change left at step 300 ===
        if step == 300 and len(vehicle_list) >= 1:
            target_vehicle = vehicle_list[0]
            if target_vehicle.current_slot:
                print("[ACTION] Execute lane change left (action 3)")
                vehicle_controller.execute_slot_action(target_vehicle.current_slot, 3)

    traci.close()
    print("[TEST] Test completed.")
