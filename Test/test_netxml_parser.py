# Test/test_netxml_parser.py

import traci
import os
import random
import sys

# Add project root to sys.path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import NetXMLParser


# ==== SUMO Configuration ====
SUMO_BINARY = "sumo-gui"  # Use "sumo" if GUI is not needed
NET_FILE = os.path.join("Sim", "joined_segments.net.xml")
RELATIVE_NET_FILE = "joined_segments.net.xml"
SUMOCFG_FILE = os.path.join("Sim", "temp.sumocfg")

# ==== Example Route Definitions (based on edge IDs) ====
ROUTE_STANDARD_TO_OFFRAMP = ["e1", "e2", "e3", "e4", "exit1"]
ROUTE_ONRAMP_TO_EXIT = ["ramp1", "e3", "e4", "e5"]


# ==== STEP 1: Generate Temporary SUMO Configuration File ====
def generate_temp_cfg(net_file, cfg_path):
    with open(cfg_path, "w") as f:
        f.write(
            f"""
            <configuration>
                <input>
                    <net-file value="{net_file}"/>
                </input>
                <time>
                    <begin value="0"/>
                    <end value="1000"/>
                </time>
            </configuration>
            """)
    print(f"[INFO] Temporary SUMO config file generated: {cfg_path}")


# ==== STEP 2: Select Lanes for Vehicle Generation by Segment Type ====
def get_spawn_lanes_by_type(segments, segment_type, exact_edge_id=None):
    lanes = []
    for seg in segments:
        if seg.segment_type == segment_type:
            if exact_edge_id is None or seg.id == exact_edge_id:
                lanes.extend(seg.lanes)
    return lanes


# ==== STEP 3: Launch SUMO Simulation and Spawn Vehicles ====
def run_sumo_and_spawn_vehicles(spawn_lanes_standard, spawn_lanes_ramp):
    print("[INFO] Launching SUMO simulation...")
    traci.start([SUMO_BINARY, "-c", SUMOCFG_FILE])
    step = 0
    veh_id = 0

    while step < 500:
        traci.simulationStep()

        if step % 10 == 0:
            # Route 1: standard_2lane → off-ramp
            if spawn_lanes_standard:
                lane = random.choice(spawn_lanes_standard)
                traci.route.add(f"route_{veh_id}", ROUTE_STANDARD_TO_OFFRAMP)
                traci.vehicle.add(f"veh{veh_id}", f"route_{veh_id}", typeID="DEFAULT_VEHTYPE")
                traci.vehicle.moveTo(f"veh{veh_id}", lane.id, 0.0)
                print(f"[INFO] Vehicle veh{veh_id} added at {lane.id} (Standard Route)")
                veh_id += 1

            # Route 2: on-ramp → right-side exit
            if spawn_lanes_ramp:
                lane = random.choice(spawn_lanes_ramp)
                traci.route.add(f"route_{veh_id}", ROUTE_ONRAMP_TO_EXIT)
                traci.vehicle.add(f"veh{veh_id}", f"route_{veh_id}", typeID="DEFAULT_VEHTYPE")
                traci.vehicle.moveTo(f"veh{veh_id}", lane.id, 0.0)
                print(f"[INFO] Vehicle veh{veh_id} added at {lane.id} (Ramp Route)")
                veh_id += 1

        step += 1

    traci.close()
    print("[INFO] Simulation completed.")


if __name__ == "__main__":
    parser = NetXMLParser("Sim/test.net.xml")
    full_lanes = parser.build_full_lanes()

    print(f"{len(full_lanes)} FullLanes constructed:")
    for fl in full_lanes:
        print("FullLane Start Lane ID: ", fl.start_lane_id)
        print("Neighbouring Lanes: ", fl.neighbor_full_lanes)
