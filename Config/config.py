# Config/config.py

default_config = {
    # ===== SUMO 配置 =====
    "sumo_config": "Sim/temp.sumocfg",
    "net_file": "Sim/test.net.xml",
    "route_file": "Sim/test.rou.xml",
    "use_gui": True,

    # ===== 环境参数 =====
    "max_steps": 10000,
    "slot_length": 8.0,
    "slot_gap": 3.0,
    "time_step": 0.1, #单位 秒

    # ===== 车辆配置 =====
    "vehicle_spawn_rate": 30,     # 每 N 步生成一辆车
    "max_vehicles": 200,          # 同时在场景中的最大车辆数
    "vehicle_type": {
        "length": 5.0,
        "max_speed": 30.0
    },

    # ===== 奖励相关参数（可选）=====
    "reward": {
        "step_penalty": -0.01,
        "forward_reward": 1.0,
        "collision_penalty": -5.0,
        "exit_reward": 2.0
    },

    # ===== Agent 控制区域 =====
    "multi-agent": True,
    "agent_zones": {
        "agent_0": {"xmin": 0, "xmax": 400, "ymin": 0, "ymax": 500},
        "agent_1": {"xmin": 400, "xmax": 800, "ymin": 0, "ymax": 500},
        "agent_2": {"xmin": 800, "xmax": 1200, "ymin": 0, "ymax": 500},
        "agent_3": {"xmin": 1200, "xmax": 1600, "ymin": 0, "ymax": 500}
    }
}
