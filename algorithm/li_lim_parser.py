"""
Parser for Li & Lim PDPTW benchmark format
Handles the original space-separated format with explicit pickup-delivery pairs
"""

import math
from typing import List
from data_loader import Node, Instance


def parse_li_lim_instance(filename: str) -> Instance:
    """
    Parse Li & Lim format PDPTW instance
    
    Format:
    Line 1: n_customers  capacity  speed (ignored)
    Lines 2+: node  x  y  demand  ready  due  service  pickup_idx  delivery_idx
    
    Returns:
        Instance object with nodes and Euclidean distance matrix
    """
    instance = Instance()
    
    with open(filename, 'r') as f:
        # Read header line
        first_line = f.readline().strip().split()
        n_customers = int(first_line[0])
        capacity = int(first_line[1])
        # third value is vehicle speed, typically ignored
        
        instance.capacity = capacity
        
        # Read node data
        nodes_data = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 9:
                continue
            
            node_data = {
                'idx': int(parts[0]),
                'x': float(parts[1]),
                'y': float(parts[2]),
                'demand': int(parts[3]),
                'ready': int(parts[4]),
                'due': int(parts[5]),
                'service': int(parts[6]),
                'pickup': int(parts[7]),
                'delivery': int(parts[8])
            }
            nodes_data.append(node_data)
        
        # Set size based on actual nodes read
        instance.size = len(nodes_data)
        
        # Create Node objects
        instance.nodes = []
        for data in nodes_data:
            node = Node()
            node.idx = data['idx']
            node.x = data['x']  # Store coordinates for distance calculation
            node.y = data['y']
            node.dem = data['demand']
            node.etw = data['ready']
            node.ltw = data['due']
            node.dur = data['service']
            
            # Pickup-delivery pairing
            # In Li & Lim format:
            # - If pickup != 0, this node is a delivery (column 7 points to pickup)
            # - If delivery != 0, this node is a pickup (column 8 points to delivery)
            if data['pickup'] != 0:
                # This is a delivery node
                node.pair = data['pickup']
            elif data['delivery'] != 0:
                # This is a pickup node
                node.pair = data['delivery']
            else:
                # This is the depot (both are 0)
                node.pair = 0
            
            instance.nodes.append(node)
        
        # Build Euclidean distance matrix (rounded to integer)
        instance.times = []
        for i in range(len(instance.nodes)):
            row = []
            for j in range(len(instance.nodes)):
                if i == j:
                    row.append(0)
                else:
                    # Euclidean distance
                    dx = instance.nodes[i].x - instance.nodes[j].x
                    dy = instance.nodes[i].y - instance.nodes[j].y
                    dist = math.sqrt(dx * dx + dy * dy)
                    # Round to integer (standard for Li & Lim)
                    row.append(int(round(dist)))
            instance.times.append(row)
        
        # Set instance name from filename
        import os
        instance.name = os.path.basename(filename).replace('.txt', '')
    
    return instance


def is_li_lim_format(filename: str) -> bool:
    """
    Detect if file is in Li & Lim format
    
    Li & Lim format starts with: n capacity speed (3 integers)
    Sartori & Buriol format starts with: SIZE: n
    """
    try:
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            
            # Check if first line has keywords (Sartori format)
            if 'SIZE' in first_line or 'CAPACITY' in first_line:
                return False
            
            # Check if first line has 3 integers (Li & Lim format)
            parts = first_line.split()
            if len(parts) >= 2:
                # Try to parse as integers
                try:
                    int(parts[0])
                    int(parts[1])
                    return True
                except ValueError:
                    return False
            
            return False
    except Exception:
        return False
