# Test/test_routexml_parser.py

import os
import sys

# Add project root to sys.path for testing purposes
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from Sumo.sumo_routexml_parser import RouteXMLParser

# Parse the .rou.xml file
parser = RouteXMLParser("Sim/test.rou.xml")

print("[All Parsed Routes]")
for route in parser.get_routes().values():
    print(route)

print("\n[Default Vehicle Type]")
print(parser.get_default_vehicle_type())
