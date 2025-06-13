# Test/test_routexml_parser.py

import traci
import os
import random
import sys

# 添加项目根目录到 sys.path 便于进行测试
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_routexml_parser import RouteXMLParser

parser = RouteXMLParser("Sim/test.rou.xml")
print("[所有路线]")
for route in parser.get_routes().values():
    print(route)

print("\n[默认车辆类型]")
print(parser.get_default_vehicle_type())