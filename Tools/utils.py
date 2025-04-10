# tools/utils.py
import os

def generate_temp_cfg(
    net_file: str = "joined_segments.net.xml",
    cfg_path: str = os.path.join("Sim", "temp.sumocfg")
):
    """
    生成 SUMO 配置文件 (.sumocfg)，用于启动仿真。
    如果不传入参数，将使用默认的路径：
      - net_file: Sim/joined_segments.net.xml
      - cfg_path: Sim/temp.sumocfg
    """
    with open(cfg_path, "w") as f:
        f.write(f"""
            <configuration>
                <input>
                    <net-file value="{net_file}"/>
                </input>
                <time>
                    <begin value="0"/>
                    <end value="1000"/>
                </time>
            </configuration>""")
    print(f"[INFO] 生成临时 SUMO 配置文件：{cfg_path}")
