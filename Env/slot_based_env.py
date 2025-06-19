import gym
import numpy as np
import traci
import subprocess
import os
import sys
import time
import math
import random

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Controller.slot_controller import SlotController
from Controller.vehicle_controller import VehicleController
from Controller.vehicle_generator import VehicleGenerator
from Controller.slot_generator import SlotGenerator
from Controller.merge_controller import MergeController
from Sumo.sumo_netxml_parser import NetXMLParser
from Sumo.sumo_routexml_parser import RouteXMLParser
from Config.config import default_config
from Tools.utils import generate_temp_cfg


class SlotBasedEnv(gym.Env):
    def __init__(self, config):
        super(SlotBasedEnv, self).__init__()
        self.config = config
        self.sumo_config = config.get("sumo_config", "Sim/temp.sumocfg")
        self.max_steps = config.get("max_steps", 1000)
        self.gui = config.get("use_gui", True)
        self.time_step = 0

        # 路网与路线解析
        net_parser = NetXMLParser(config.get("net_file", "Sim/test.net.xml"))
        self.full_lanes = net_parser.build_full_lanes()
        self.lane_dict = net_parser.lane_dict

        route_parser = RouteXMLParser(config.get("route_file", "Sim/test.rou.xml"))
        self.routes = route_parser.get_routes()
        self.route_groups = route_parser.get_route_groups()
        self.default_vtype = route_parser.get_default_vehicle_type()

        self.sumo_running = False

    def _start_sumo(self):
        if not self.sumo_running:
            generate_temp_cfg()
            sumo_binary = "sumo-gui" if self.gui else "sumo"
            sumo_cmd = [sumo_binary, "-c", self.sumo_config]
            traci.start(sumo_cmd)
            self.sumo_running = True

    def reset(self):
        if self.sumo_running:
            traci.close()
            self.sumo_running = False
            time.sleep(0.2)
        self._start_sumo()
        traci.simulationStep()

        self.time_step = 0

        self.slot_generator = SlotGenerator()
        self.slot_generator.generate_slots_for_all_full_lanes(self.full_lanes)
        self.slot_controller = SlotController(self.slot_generator, self.full_lanes)

        self.vehicle_generator = VehicleGenerator(self.routes, self.default_vtype)
        self.rendered_slots = set()
        self.rendered_vehicles = set()
        self.vehicle_list = []

        for fl in self.full_lanes:
            for slot in fl.slots:
                if slot.center:
                    x, y = slot.center
                    try:
                        traci.poi.add(slot.id, x, y, color=(255, 0, 0), layer=5)
                        traci.poi.setParameter(slot.id, "label", slot.id)
                        self.rendered_slots.add(slot.id)
                    except:
                        pass

        self.vehicle_controller = VehicleController(self.vehicle_list, self.route_groups)
        self.ramp_to_fulllane_map = {
            "on_ramp1": "e2_0",
            "-on_ramp1": "-e6_0"
        }
        self.merge_controller = MergeController(self.full_lanes, self.ramp_to_fulllane_map, safety_gap=5.0)
        self.slot_list = [slot for fl in self.full_lanes for slot in fl.slots]

        observation = self._get_observation()
        info = {}
        return observation, info

    def step(self, actions=[]):
        # ✅ 判断 multi-agent 模式
        if self.config.get("multi-agent", False):
            for agent_id, agent_actions in actions.items():
                for slot_id, action_type in agent_actions:
                    if 0 <= slot_id < len(self.slot_list):
                        slot = self.slot_list[slot_id]
                        if slot.occupied and not slot.busy:
                            self.vehicle_controller.execute_slot_action(slot, action_type)
        else:
            for slot_id, action_type in actions:
                if 0 <= slot_id < len(self.slot_list):
                    slot = self.slot_list[slot_id]
                    if slot.occupied and not slot.busy:
                        self.vehicle_controller.execute_slot_action(slot, action_type)

        # 环境推进
        traci.simulationStep()
        removed = self.slot_controller.step()
        self.vehicle_controller.step()
        self.merge_controller.step(self.vehicle_list)

        # ✅ 确保 self.slot_list 是最新的
        self.slot_list = [slot for fl in self.full_lanes for slot in fl.slots]

        # slot 可视化
        for fl in self.full_lanes:
            for slot in fl.slots:
                if slot.center:
                    if slot.id in self.rendered_slots:
                        try:
                            traci.poi.setPosition(slot.id, *slot.center)
                        except:
                            pass
                    else:
                        try:
                            traci.poi.add(slot.id, *slot.center, color=(255, 0, 0), layer=5)
                            traci.poi.setParameter(slot.id, "label", slot.id)
                            self.rendered_slots.add(slot.id)
                        except:
                            pass

        # slot 移除
        for old_slot, _ in removed:
            try:
                traci.poi.remove(old_slot.id)
                self.rendered_slots.discard(old_slot.id)
            except:
                pass

        # 每 30 步添加车辆
        if self.time_step % 30 == 0:
            selected_route = self.vehicle_generator.select_random_route()
            entry_edge = selected_route.edges[0]
            candidate_lanes = [lane for lane in self.lane_dict.values() if lane.id.startswith(entry_edge + "_")]
            if not candidate_lanes:
                print(f"[WARN] 无法在 edge {entry_edge} 上找到可用 lane")
            selected_lane = random.choice(candidate_lanes)
            is_ramp = "ramp" in selected_lane.id.lower()

            vehicle = None
            if is_ramp:
                vehicle = self.vehicle_generator.generate_vehicle(slot=None, route=selected_route)
            else:
                target_fl = next((fl for fl in self.full_lanes if fl.start_lane_id == selected_lane.id), None)
                if not target_fl or not target_fl.slots:
                    print(f"[INFO] 未找到合适 FullLane 或无可用 slot：{selected_lane.id}")
                slot = target_fl.slots[0]
                if getattr(slot, "occupied", False):
                    print(f"[INFO] slot {slot.id} 已被占用，跳过生成")
                vehicle = self.vehicle_generator.generate_vehicle(slot=slot, route=selected_route)

            if vehicle and vehicle.id not in self.rendered_vehicles:
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
                        traci.vehicle.setLaneChangeMode(vehicle.id, 256)
                        traci.vehicle.setSpeedMode(vehicle.id, 0)
                        traci.vehicle.setSpeed(vehicle.id, vehicle.speed)

                        heading_rad = math.radians(slot.heading)
                        x_center, y_center = slot.center
                        vehicle_length = vehicle.vehicle_type.length
                        x_front = x_center + (vehicle_length / 2.0) * math.cos(heading_rad)
                        y_front = y_center + (vehicle_length / 2.0) * math.sin(heading_rad)
                        edge_id = slot.lane.id.rsplit("_", 1)[0]
                        lane_index = int(slot.lane.id.rsplit("_", 1)[-1])
                        traci.vehicle.moveToXY(vehicle.id, edgeID=edge_id, laneIndex=lane_index,
                                            x=x_front, y=y_front, angle=slot.heading, keepRoute=1)
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

                    self.rendered_vehicles.add(vehicle.id)
                    self.vehicle_list.append(vehicle)
                    print(f"[ADD VEH] {vehicle.id} 添加成功，路线 {selected_route.id}")
                except Exception as e:
                    print(f"[WARN] 添加 {vehicle.id} 失败：{e}")

        self.time_step += 1

        observation = self._get_observation()
        reward = self._get_reward()
        done = self.time_step >= self.max_steps
        info = {}

        return observation, reward, done, info

    def _get_observation(self):
        all_slot_data = []

        for idx, slot in enumerate(self.slot_list):
            if slot.center is None:
                continue
            x, y = slot.center
            controllable = 1.0 if slot.occupied and not slot.busy else 0.0
            all_slot_data.append([idx, x, y, controllable])

        obs_array = np.array(all_slot_data, dtype=np.float32)

        # 判断是否是 multi-agent 模式
        if self.config.get("multi-agent", False):
            agent_obs = {}
            zones = self.config.get("agent_zones", {})
            for agent_id, zone in zones.items():
                xmin, xmax = zone["xmin"], zone["xmax"]
                ymin, ymax = zone["ymin"], zone["ymax"]
                agent_slot_data = obs_array[
                    (obs_array[:, 1] >= xmin) & (obs_array[:, 1] < xmax) &
                    (obs_array[:, 2] >= ymin) & (obs_array[:, 2] < ymax)
                ]
                agent_obs[agent_id] = agent_slot_data
            return agent_obs
        else:
            return obs_array

    def _get_reward(self):
        return 0.0

    def close(self):
        if self.sumo_running:
            traci.close()
            self.sumo_running = False

    def render(self, mode='human'):
        pass


if __name__ == "__main__":
    env = SlotBasedEnv(default_config)
    obs, info = env.reset()
    print("初始状态：", {k: v.shape for k, v in obs.items()} if isinstance(obs, dict) else obs.shape)
    max_steps = default_config["max_steps"]
    done = False

    # Multi-Agent 模式测试
    if default_config.get("multi-agent", False):
        while not done:
            actions = {}
            for agent_id, agent_obs in obs.items():
                agent_actions = []
                for i in range(agent_obs.shape[0]):
                    slot_id = int(agent_obs[i][0])
                    if agent_obs[i][3] == 1.0:
                        action_type = random.choice([0, 1, 2, 3, 4])  # stay, forward, backward, change left, change right
                        agent_actions.append((slot_id, action_type))
                actions[agent_id] = agent_actions
            obs, reward, done, info = env.step(actions)
    else:
        while not done:
            actions = []
            for i in range(obs.shape[0]):
                slot_id = int(obs[i][0])
                if obs[i][3] == 1.0:
                    action_type = random.choice([0, 1, 2, 3, 4])  # stay, forward, backward, change left, change right
                    actions.append((slot_id, action_type))
            obs, reward, done, info = env.step(actions)

    env.close()
