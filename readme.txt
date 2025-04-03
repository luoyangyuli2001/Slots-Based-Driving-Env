Slot-Based Driving Environment (SUMO Simulation Framework)
===========================================================

Overview
--------
This project implements a prototype of a slot-based driving environment using the SUMO traffic simulator. A slot is a virtual container unit that continuously flows along road lanes. Vehicles can align to and follow slots to simplify trajectory planning, enabling more structured traffic management and future reinforcement learning integration.

Goals include modular lane control, dynamic merging/diverging, and rule-based or learning-based scheduling of vehicle-slot interactions.

Current Features
----------------
✔ Modular network composed of standard, ramp, and exit segments  
✔ Automatic parsing of .net.xml files into structured Segment / Lane / Slot objects  
✔ Continuous slot movement across multiple connected segments via `next_lane`  
✔ Slot center point visualized in SUMO GUI using POIs  
✔ Independent vehicle generation for testing  

Project Structure
-----------------
SlotBasedEnv/
├── Controller/
│   ├── slot_generator.py              # Slot generation for all valid lanes
│   ├── slot_controller.py             # Manages dynamic slot movement
│
├── Entity/
│   ├── segment.py                     # Segment data model
│   ├── lane.py                        # Lane entity (includes `next_lane`)
│   ├── slot.py                        # Slot definition (length, center, speed, etc.)
│
├── Sumo/
│   ├── sumo_netxml_parser.py          # .net.xml parser with next_lane linker
│
├── Tools/
│   ├── utils.py                       # Utility functions (e.g., generate SUMO config)
│
├── Test/
│   ├── test_slot_controller_generator.py  # Simulation and visualization test
│
├── Sim/
│   ├── joined_segments.net.xml        # Example merged highway network
│   ├── temp.sumocfg                   # Temporary SUMO configuration
│
└── README.txt                         # This project documentation

Design Assumptions
------------------
- Right-hand vehicle design (left-side driving, as in the UK/Ireland)
- Lane numbering is reversed (rightmost lane = index 0)
- Slot transition is based on explicit next_lane setup, not SUMO default routing
- Only standard (main road) lanes generate slots; ramps and exits are excluded

Known Issues
------------
1. Slot-to-slot transmission across segments may incur 1-step visual delay due to time_step granularity  
2. SUMO uses a left-hand traffic default; visual alignment of right-hand lane logic requires manual offset correction

Future Plans
------------
- Slot lifecycle control (recycle, regeneration)
- Vehicle-slot linking logic (tracking, occupying, releasing)
- Lane-switching slot logic for merge/split scenarios
- Data export and trajectory analytics

Author
------
GitHub: https://github.com/luoyangyuli2001/Slots-Based-Driving-Env.git  
Author: @luoyangyuli2001 (Trinity College Dublin)



Slot-Based Driving Environment（基于 SUMO 的 Slot 驱动仿真环境）
==================================================================

项目简介
--------
本项目旨在基于 SUMO 模拟构建一个“slot-based driving system”，通过引入 slot（槽位）来代替传统车辆路径调度。Slot 作为一种虚拟交通单位，可以在道路上连续流动，车辆将基于 slot 实现智能调度和控制。

该系统的设计目标包括：提高道路可控性、支持多车道结构、支持车道变换与融合逻辑、简化多智能体调度的模型基础。

当前功能
--------
✔ 路网结构模块化（标准路段、汇入汇出段可拼接）
✔ 支持自动解析 .net.xml 并生成 Segment / Lane / Slot 等结构化对象
✔ Slot 可在主干道多个 segment 之间连续流动（基于 next_lane 引用）
✔ Slot 的位置会在 SUMO-GUI 中以 POI 点可视化展示
✔ 车辆生成与 slot 可解耦，未来支持绑定逻辑

项目结构
--------
SlotBasedEnv/
├── Controller/
│   ├── slot_generator.py              # 用于主干道 slot 的批量生成
│   ├── slot_controller.py             # 控制 slot 在仿真中的动态移动
│
├── Entity/
│   ├── segment.py                     # Segment 实体定义
│   ├── lane.py                        # Lane 实体定义（含 next_lane 引用）
│   ├── slot.py                        # Slot 实体定义（含 center、speed 等）
│
├── Sumo/
│   ├── sumo_netxml_parser.py          # 用于解析 .net.xml 并建立结构与连接
│
├── Tools/
│   ├── utils.py                       # 通用工具函数（如临时配置生成）
│
├── Test/
│   ├── test_slot_controller_generator.py  # 用于 slot 可视化测试与控制测试
│
├── Sim/
│   ├── joined_segments.net.xml        # 拼接好的测试路网
│   ├── temp.sumocfg                   # 自动生成的 SUMO 配置文件
│
└── README.txt                         # 当前项目说明文档

关键设计
--------
- 使用右舵左行的交通逻辑（靠左行驶）
- Lane 的编号顺序与实际道路顺序相反（编号从右到左）
- next_lane 显式设置而非依赖 SUMO 默认连接逻辑
- Slot 仅生成于主干道（standard 类型），ramp 和 exit 路段不生成 slot

已知问题
--------
1. Slot 在 segment 之间切换时存在一帧延迟，可能由 time_step 引起
2. SUMO 默认假设为左舵环境，与本系统设计存在方向性差异，需手动调整 lane 编号对齐方式

计划扩展
--------
- Slot 的自动补充与生命周期管理
- Slot 与车辆之间的绑定与占用逻辑
- 多车道之间的 slot 动态切换与并道处理
- 数据导出与 slot 流轨迹分析

作者
----
GitHub: https://github.com/luoyangyuli2001/Slots-Based-Driving-Env.git
作者：@luoyangyuli2001（Trinity College Dublin）
