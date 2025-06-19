# tools/utils.py
import os

def generate_temp_cfg(
    net_file: str = "test.net.xml",
    route_file: str = "test.rou.xml",
    cfg_path: str = os.path.join("Sim", "temp.sumocfg")
):
    """
    Generates a SUMO configuration file (.sumocfg) for starting the simulation.
    If no parameters are passed, the default path will be used:
      - net_file: Sim/joined_segments.net.xml
      - cfg_path: Sim/temp.sumocfg
    """
    with open(cfg_path, "w") as f:
        f.write(f"""
            <configuration>
                <input>
                    <net-file value="{net_file}"/>
                    <route-files value="{route_file}"/>
                </input>
                <time>
                    <begin value="0"/>
                    <end value="1000"/>
                    <step-length value="0.1"/>
                </time>
            </configuration>""")
    print(f"[INFO] Generate SUMO Config File：{cfg_path}")

