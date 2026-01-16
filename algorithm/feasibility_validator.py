"""
Strict feasibility validator for PDPTW solutions
Uses the official validator but adds detailed violation reporting
"""

import sys
import os
from typing import Tuple, List, Dict

# Add parent directory to path to access validator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from validator.validator import validate_solution as official_validate_solution
from data_loader import Instance, Solution


class FeasibilityValidator:
    """Strict validator with detailed violation reporting"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        
    def validate_solution(self, solution: Solution) -> Tuple[bool, List[str]]:
        """
        Validate solution with detailed violation reporting
        
        Returns:
            (is_feasible, violations) where violations is a list of violation messages
        """
        violations = []
        
        # Convert Solution to format expected by official validator
        visited = [0] * self.instance.size
        is_feasible = True
        
        for route_idx, route in enumerate(solution.routes):
            # Validate each route
            route_violations = self._validate_route(route, route_idx, visited)
            if route_violations:
                violations.extend(route_violations)
                is_feasible = False
        
        # Check if all nodes are visited exactly once
        missing_nodes = []
        for i in range(1, self.instance.size):
            if visited[i] == 0:
                missing_nodes.append(i)
            elif visited[i] > 1:
                violations.append(f"Node {i} visited {visited[i]} times (duplicate)")
                is_feasible = False
        
        if missing_nodes:
            violations.append(f"Nodes not visited: {missing_nodes}")
            is_feasible = False
        
        return is_feasible, violations
    
    def _validate_route(self, route: List[int], route_idx: int, visited: List[int]) -> List[str]:
        """Validate a single route and return list of violations"""
        violations = []
        
        if not route:
            return violations
        
        time = 0
        load = 0
        prev_node = 0  # depot
        visited_pickups_in_route = set()
        
        for pos, node_id in enumerate(route):
            # Check node bounds
            if node_id < 0 or node_id >= self.instance.size:
                violations.append(f"Route {route_idx}: Invalid node ID {node_id} at position {pos}")
                continue
            
            # Check duplicate visits
            if visited[node_id] > 0:
                violations.append(f"Route {route_idx}: Node {node_id} already visited")
            visited[node_id] += 1
            
            node = self.instance.nodes[node_id]
            
            # Update time
            travel_time = self.instance.get_travel_time(prev_node, node_id)
            time += travel_time
            
            # Check time window
            arrival_time = max(time, node.etw)
            if arrival_time > node.ltw:
                violations.append(
                    f"Route {route_idx}: Time window violation at node {node_id} "
                    f"(arrival {arrival_time} > latest {node.ltw})"
                )
            
            # Check pickup-delivery precedence
            if node.is_delivery():
                pickup_idx = node.pair
                if pickup_idx not in visited_pickups_in_route:
                    violations.append(
                        f"Route {route_idx}: Delivery {node_id} before pickup {pickup_idx}"
                    )
            
            # Update load and check capacity
            load += node.dem
            if load > self.instance.capacity:
                violations.append(
                    f"Route {route_idx}: Capacity exceeded at node {node_id} "
                    f"(load {load} > capacity {self.instance.capacity})"
                )
            if load < 0:
                violations.append(
                    f"Route {route_idx}: Negative load {load} at node {node_id}"
                )
            
            # Mark pickup as visited
            if node.is_pickup():
                visited_pickups_in_route.add(node_id)
            
            # Update time after service
            time = arrival_time + node.dur
            prev_node = node_id
        
        # Check return to depot
        if route:
            return_time = time + self.instance.get_travel_time(prev_node, 0)
            depot = self.instance.nodes[0]
            if return_time > depot.ltw:
                violations.append(
                    f"Route {route_idx}: Return to depot too late "
                    f"(time {return_time} > depot close {depot.ltw})"
                )
        
        return violations
    
    def validate_with_official(self, solution: Solution) -> Tuple[bool, str, int, int]:
        """
        Use the official validator from validator/validator.py
        
        Returns:
            (is_valid, message, num_vehicles, cost)
        """
        try:
            # Create a mock instance object with the required format
            class MockInstance:
                def __init__(self, real_instance):
                    self.size = real_instance.size
                    self.capacity = real_instance.capacity
                    self.nodes = real_instance.nodes
                    self.times = real_instance.times
            
            mock_inst = MockInstance(self.instance)
            
            # Ensure routes include depot wrapping
            wrapped_solution = Solution()
            wrapped_solution.inst_name = solution.inst_name
            wrapped_solution.authors = solution.authors
            wrapped_solution.routes = []
            
            for route in solution.routes:
                if route and route[0] != 0:
                    wrapped_route = [0] + route + [0]
                else:
                    wrapped_route = route
                wrapped_solution.routes.append(wrapped_route)
            
            result = official_validate_solution(mock_inst, wrapped_solution)
            return result
            
        except Exception as e:
            return (False, f"Validator error: {str(e)}", 0, 0)


def validate_solution(solution: Solution, instance: Instance) -> Tuple[bool, List[str]]:
    """
    Convenience function for quick validation
    
    Returns:
        (is_feasible, violations)
    """
    validator = FeasibilityValidator(instance)
    return validator.validate_solution(solution)
