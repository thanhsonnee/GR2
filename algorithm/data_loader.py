"""
Data loader classes for PDPTW instances and solutions
Adapted from the validator.py code to understand instance structure
"""

import re
import math
from typing import List, Dict, Tuple, Optional


class Node:
    """Represents a node in PDPTW instance"""
    def __init__(self):
        self.idx = 0        # node index  
        self.lat = 0.0      # latitude (Sartori & Buriol format)
        self.long = 0.0     # longitude (Sartori & Buriol format)
        self.x = 0.0        # x coordinate (Li & Lim format)
        self.y = 0.0        # y coordinate (Li & Lim format)
        self.dem = 0        # demand (positive: pickup, negative: delivery)
        self.etw = 0        # earliest time window start
        self.ltw = 0        # latest time window start  
        self.dur = 0        # service duration
        self.pair = 0       # pickup-delivery pair
        
    def is_pickup(self) -> bool:
        return self.dem > 0
        
    def is_delivery(self) -> bool:
        return self.dem < 0
        
    def is_depot(self) -> bool:
        return self.idx == 0


class Instance:
    """Represents a PDPTW instance"""
    def __init__(self):
        self.name = ""
        self.location = ""
        self.size = 0                    # number of nodes including depot
        self.capacity = 0               # vehicle capacity
        self.distribution = ""
        self.depot_type = ""
        self.route_time = 0
        self.time_window = 0
        self.nodes = []                 # list of Node objects
        self.times = []                 # travel time matrix
        
    @property
    def distance_matrix(self):
        """Compatibility alias for code that expects distance_matrix."""
        return self.times

    def read_from_file(self, filename: str):
        """
        Read instance from file - auto-detects format
        Supports both Sartori & Buriol and Li & Lim formats
        """
        # Auto-detect format
        from li_lim_parser import is_li_lim_format, parse_li_lim_instance
        
        if is_li_lim_format(filename):
            # Use Li & Lim parser
            parsed_instance = parse_li_lim_instance(filename)
            # Copy all attributes to self
            self.name = parsed_instance.name
            self.size = parsed_instance.size
            self.capacity = parsed_instance.capacity
            self.nodes = parsed_instance.nodes
            self.times = parsed_instance.times
            return
        
        # Otherwise, use Sartori & Buriol parser (original code below)
        with open(filename, "r") as f:
            # Read header section until we hit the NODES marker
            for _ in range(100):
                line = f.readline()
                if not line:
                    break
                stripped = line.strip()
                fields = stripped.split()
                
                if stripped == "NODES":
                    break
                elif len(fields) >= 2:
                    field_name = fields[0].rstrip(":").upper()
                    field_value = " ".join(fields[1:])
                    
                    if field_name == "NAME":
                        self.name = field_value
                    elif field_name == "LOCATION":
                        self.location = field_value
                    elif field_name == "SIZE":
                        self.size = int(field_value)
                    elif field_name == "CAPACITY":
                        self.capacity = int(field_value)
                    elif field_name == "DISTRIBUTION":
                        self.distribution = field_value
                    elif field_name == "DEPOT":
                        self.depot_type = field_value.upper().replace(':', '')
                    elif field_name == "ROUTE-TIME":
                        self.route_time = int(field_value)
                    elif field_name == "TIME-WINDOW":
                        self.time_window = int(field_value)

            # Read NODES section
            self.nodes = []
            for _ in range(self.size):
                line = f.readline().strip()
                if not line:  # Skip empty lines
                    continue
                fields = line.split()
                
                if len(fields) < 7:  # Skip lines that don't have enough fields
                    continue
                    
                node = Node()
                node.idx = int(fields[0])
                node.lat = float(fields[1])
                node.long = float(fields[2])
                node.dem = int(fields[3])
                node.etw = int(fields[4])
                node.ltw = int(fields[5])
                node.dur = int(fields[6])
                
                # Calculate pickup-delivery pair
                if node.dem > 0:  # pickup
                    pair_id = int(fields[7]) if len(fields) > 7 else 0
                    node.pair = pair_id if pair_id > 0 else node.idx + int(self.size//2)
                elif node.dem < 0:  # delivery  
                    pair_id = int(fields[8]) if len(fields) > 8 else 0
                    node.pair = pair_id if pair_id > 0 else node.idx - int(self.size//2)
                    
                self.nodes.append(node)

            # Read EDGES section
            line = f.readline().strip()
            while line != "EDGES":
                line = f.readline().strip()
                
            # Read travel time matrix
            self.times = []
            for _ in range(self.size):
                line = f.readline()
                row = [int(x) for x in line.split()]
                self.times.append(row)
                
    def get_travel_time(self, from_node: int, to_node: int) -> int:
        """Get travel time between two nodes"""
        try:
            # Bounds checking
            if (from_node < 0 or from_node >= len(self.times) or 
                to_node < 0 or to_node >= len(self.times[0]) if self.times else True):
                print(f"Warning: Invalid node indices: {from_node} -> {to_node}")
                return 9999  # Large penalty for invalid access
            return self.times[from_node][to_node]
        except (IndexError, TypeError):
            print(f"Error accessing travel time matrix: {from_node} -> {to_node}")
            return 9999
        
    def get_node(self, idx: int) -> Node:
        """Get node by index"""
        return self.nodes[idx]
            
    def get_pickup_delivery_pairs(self) -> List[Tuple[int, int]]:
        """Get all pickup-delivery pairs as tuples (pickup_idx, delivery_idx)"""
        pairs = []
        depot_nodes = [n for n in self.nodes if not n.is_depot()]
        
        for node in depot_nodes:
            if node.is_pickup():
                pairs.append((node.idx, node.pair))
                
        return pairs
        
    def get_pickups(self) -> List[Node]:
        """Get all pickup nodes"""
        return [n for n in self.nodes if n.is_pickup()]
        
    def get_deliveries(self) -> List[Node]:
        """Get all delivery nodes"""
        return [n for n in self.nodes if n.is_delivery()]
        
        
class Solution:
    """Represents a PDPTW solution"""
    def __init__(self):
        self.inst_name = ""
        self.authors = ""
        self.date = ""
        self.reference = ""
        self.routes = []               # list of routes, each route is list of node indices
        
    def read_from_file(self, filename: str):
        """Read solution from file"""
        with open(filename, "r", errors='ignore') as f:
            self.routes = []
            
            # Read header information
            for _ in range(5):
                line = f.readline()
                if ":" in line:
                    parts = line.split(" : ")
                    if len(parts) >= 2:
                        field = parts[0].strip()
                        value = parts[1].strip().replace('\n', '')
                        
                        if field == "Instance name":
                            self.inst_name = value
                        elif field == "Authors":
                            self.authors = value
                        elif field == "Date":
                            self.date = value
                        elif field == "Reference":
                            self.reference = field

            # Read routes
            for line in f:
                if ":" in line and "Route" in line:
                    # Extract sequence from "Route X : sequence"
                    sequence_part = line.split(":")[1]
                    sequence = sequence_part.split(" ")
                    
                    # Filter out empty strings and clean node IDs
                    route = []
                    for node_str in sequence:
                        node_str = re.sub(r"[\n\t\s]*", "", node_str)
                        if node_str:
                            try:
                                node_id = int(node_str)
                                route.append(node_id)
                            except ValueError:
                                continue
                    
                    if route:  # Only add non-empty routes
                        self.routes.append(route)
                        
    def get_cost(self, instance: Instance) -> int:
        """Calculate total cost of solution"""
        total_cost = 0
        
        for route in self.routes:
            if len(route) == 1:  # Single depot route
                continue
                
            # Add travel from depot to first node
            prev_node = 0
            for node_id in route:
                total_cost += instance.get_travel_time(prev_node, node_id)
                prev_node = node_id
                
            # Add travel from last node back to depot  
            if route[-1] != 0:
                total_cost += instance.get_travel_time(route[-1], 0)
                
        return total_cost
        
    def get_num_vehicles(self) -> int:
        """Get number of vehicles (routes) used"""
        return len(self.routes)


if __name__ == "__main__":
    # Test the data loader
    print("Data loader classes implemented successfully")
