# test_netxml_parser.py

import traci
import os
import random
import sys

# 添加项目根目录到 sys.path 便于进行测试
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_netxml_parser import parse_netxml


# ==== SUMO 配置 ====
SUMO_BINARY = "sumo-gui"  # 如果不需要图形界面可改为 "sumo"
NET_FILE = os.path.join("Sim", "joined_segments.net.xml")
RELATIVE_NET_FILE = "joined_segments.net.xml"
SUMOCFG_FILE = os.path.join("Sim", "temp.sumocfg")

# ==== 路线定义（基于 edge ID） ====
ROUTE_STANDARD_TO_OFFRAMP = ["e1", "e2", "e3", "e4", "exit1"]
ROUTE_ONRAMP_TO_EXIT = ["ramp1", "e3", "e4", "e5"]

# ==== STEP 1: 生成配置文件 ====
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
    print(f"[INFO] 已生成 SUMO 配置文件：{cfg_path}")

# ==== STEP 2: 获取用于生成车辆的 lane ====
def get_spawn_lanes_by_type(segments, segment_type, exact_edge_id=None):
    lanes = []
    for seg in segments:
        if seg.segment_type == segment_type:
            if exact_edge_id is None or seg.id == exact_edge_id:
                lanes.extend(seg.lanes)
    return lanes

# ==== STEP 3: 启动 TraCI 模拟 ====
def run_sumo_and_spawn_vehicles(spawn_lanes_standard, spawn_lanes_ramp):
    print("[INFO] 正在启动 SUMO 仿真...")
    traci.start([SUMO_BINARY, "-c", SUMOCFG_FILE])
    step = 0
    veh_id = 0

    while step < 500:
        traci.simulationStep()

        if step % 10 == 0:
            # 路线 1：standard_2lane → off-ramp
            if spawn_lanes_standard:
                lane = random.choice(spawn_lanes_standard)
                traci.route.add(f"route_{veh_id}", ROUTE_STANDARD_TO_OFFRAMP)
                traci.vehicle.add(f"veh{veh_id}", f"route_{veh_id}", typeID="DEFAULT_VEHTYPE")
                traci.vehicle.moveTo(f"veh{veh_id}", lane.id, 0.0)
                print(f"[INFO] 添加 veh{veh_id} @ {lane.id}（标准路线）")
                veh_id += 1

            # 路线 2：on-ramp → 右侧出口
            if spawn_lanes_ramp:
                lane = random.choice(spawn_lanes_ramp)
                traci.route.add(f"route_{veh_id}", ROUTE_ONRAMP_TO_EXIT)
                traci.vehicle.add(f"veh{veh_id}", f"route_{veh_id}", typeID="DEFAULT_VEHTYPE")
                traci.vehicle.moveTo(f"veh{veh_id}", lane.id, 0.0)
                print(f"[INFO] 添加 veh{veh_id} @ {lane.id}（Ramp路线）")
                veh_id += 1

        step += 1

    traci.close()
    print("[INFO] 仿真结束。")


if __name__ == "__main__":
    print("[INFO] 解析路网中...")
    segments = parse_netxml(NET_FILE)
    print(f"[INFO] 成功解析 {len(segments)} 个 Segment")

    generate_temp_cfg(RELATIVE_NET_FILE, SUMOCFG_FILE)
    # 获取 spawn lanes
    standard_lanes = get_spawn_lanes_by_type(segments, segment_type="standard", exact_edge_id="e1")
    ramp_lanes = get_spawn_lanes_by_type(segments, segment_type="on_ramp")
    run_sumo_and_spawn_vehicles(standard_lanes, ramp_lanes)
