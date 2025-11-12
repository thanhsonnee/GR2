"""
Local search operators for PDPTW
Implements various neighborhood structures for improvement algorithms
"""

import random
import copy
from typing import List, Tuple, Optional, Set
from data_loader import Instance, Node
from solution_encoder import Solution
from construction_heuristic import ConstructionHeuristic


class LocalSearch:
    """Local search algorithms for PDPTW optimization"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        self.pair_map = self._build_pair_map()
        
    def _build_pair_map(self) -> dict:
        """Build mapping from pickup to delivery nodes and vice versa"""
        pair_map = {}
        for node in self.instance.nodes:
            if node.pair > 0:
                pair_map[node.idx] = node.pair
        return pair_map
    
    def relocate_pickup_delivery_pair(self, solution: Solution, 
                                    pickup_idx: int, delivery_idx: int, 
                                    target_route_idx: int, position: int) -> Optional[Solution]:
        """
        Relocate a pickup-delivery pair from one route to another route at given position
        """
        new_solution = copy.deepcopy(solution)
        
        # Find source route and remove the pair
        source_route_idx = -1
        pickup_pos_in_source = -1
        delivery_pos_in_source = -1
        
        for route_idx, route in enumerate(new_solution.routes):
            if pickup_idx in route:
                pickup_pos_in_source = route.index(pickup_idx)
                source_route_idx = route_idx
                
                # Find delivery position
                for i, node_idx in enumerate(route):
                    if node_idx == delivery_idx:
                        delivery_pos_in_source = i
                        break
                break
        
        if source_route_idx == -1:
            return None
            
        # Remove pickup and delivery from source route
        source_route = new_solution.routes[source_route_idx]
        # Remove delivery first to avoid index shifting
        if delivery_pos_in_source > pickup_pos_in_source:
            source_route.pop(delivery_pos_in_source)
            source_route.pop(pickup_pos_in_source)
        else:
            source_route.pop(pickup_pos_in_source)
            source_route.pop(delivery_pos_in_source)
            
        # If source route becomes empty, remove it
        if not source_route or source_route == [0]:
            new_solution.routes.pop(source_route_idx)
            if target_route_idx > source_route_idx:
                target_route_idx -= 1
                
        # Insert into target route
        if target_route_idx >= len(new_solution.routes):
            # Create new route
            new_solution.routes.append([pickup_idx, delivery_idx])
        else:
            target_route = new_solution.routes[target_route_idx]
            if position > len(target_route):
                position = len(target_route)
                
            # Insert pickup and delivery maintaining precedence
            target_route.insert(position, pickup_idx)
            
            # Find good position for delivery (after pickup)
            delivery_position = self._find_best_delivery_position(target_route, position, delivery_idx)
            target_route.insert(delivery_position, delivery_idx)
            
        return new_solution
    
    def _find_best_delivery_position(self, route: List[int], pickup_pos: int, delivery_idx: int) -> int:
        """Find best position to insert delivery node after pickup"""
        delivery_node = self.instance.nodes[delivery_idx]
        pickup_node = self.instance.nodes[pickup_idx]
        
        best_pos = pickup_pos + 1
        
        # Try positions after pickup
        for pos in range(pickup_pos + 1, len(route) + 1):
            # Check feasibility
            temp_route = route[:pos] + [delivery_idx] + route[pos:]
            if self._is_feasible_route(temp_route):
                best_pos = pos
            else:
                break
                
        return best_pos
    
    def exchange_pickup_delivery_pairs(self, solution: Solution,
                                     pair1_pickup: int, pair1_delivery: int,
                                     pair2_pickup: int, pair2_delivery: int) -> Optional[Solution]:
        """Exchange two pickup-delivery pairs between routes"""
        new_solution = copy.deepcopy(solution)
        
        # Find routes containing the pairs
        route1_idx = self._find_route_containing_node(pair1_pickup, new_solution.routes)
        route2_idx = self._find_route_containing_node(pair2_pickup, new_solution.routes)
        
        if route1_idx == -1 or route2_idx == -1:
            return None
            
        route1 = new_solution.routes[route1_idx]
        route2 = new_solution.routes[route2_idx]
        
        # Remove pair1 from route1
        route1_copy = [node for node in route1 if node not in [pair1_pickup, pair1_delivery]]
        
        # Remove pair2 from route2
        route2_copy = [node for node in route2 if node not in [pair2_pickup, pair2_delivery]]
        
        # Create new routes by exchanging pairs
        new_route1 = self._merge_pairs_into_route(route1_copy, [(pair2_pickup, pair2_delivery)])
        new_route2 = self._merge_pairs_into_route(route2_copy, [(pair1_pickup, pair1_delivery)])
        
        # Update solution
        new_solution.routes[route1_idx] = new_route1
        new_solution.routes[route2_idx] = new_route2
        
        return new_solution
    
    def two_opt_route(self, route: List[int]) -> List[int]:
        """Apply 2-opt to a single route"""
        if len(route) < 4:  # Need at least 4 nodes for 2-opt to make sense
            return route
            
        best_route = route[:]
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    # Create new route by reversing segment i to j
                    new_route = route[:]
                    new_route[i:j+1] = reversed(new_route[i:j+1])
                    
                    if (self._is_feasible_route(new_route) and 
                        self._calculate_route_cost(new_route) < self._calculate_route_cost(best_route)):
                        best_route = new_route
                        route = new_route  # Update for next iteration
                        improved = True
                        break
                if improved:
                    break
                    
        return best_route
    
    def or_opt_pickup_delivery(self, solution: Solution) -> Optional[Solution]:
        """
        OR-opt move: relocate a pickup-delivery pair to different position within same route
        or to different route
        """
        best_solution = solution
        improved = True
        
        while improved:
            improved = False
            
            # Try relocating each pair
            for route_idx, route in enumerate(solution.routes):
                pairs_in_route = self._get_pickup_delivery_pairs_in_route(route)
                
                for pickup_idx, delivery_idx in pairs_in_route:
                    # Try different positions within same route
                    for new_position in range(len(route) + 1):
                        if new_position == self._get_node_position(route, pickup_idx):
                            continue
                            
                        new_sol = self.relocate_pickup_delivery_pair(
                            best_solution, pickup_idx, delivery_idx, route_idx, new_position
                        )
                        
                        if (new_sol and self._is_valid_solution(new_sol) and 
                            self._calculate_total_cost(new_sol) < self._calculate_total_cost(best_solution)):
                            best_solution = new_sol
                            improved = True
                            break
                    
                    # Try relocating to different routes
                    for target_route_idx in range(len(solution.routes)):
                        if target_route_idx == route_idx:
                            continue
                            
                        for position in range(len(solution.routes[target_route_idx]) + 1):
                            new_sol = self.relocate_pickup_delivery_pair(
                                best_solution, pickup_idx, delivery_idx, target_route_idx, position
                            )
                            
                            if (new_sol and self._is_valid_solution(new_sol) and 
                                self._calculate_total_cost(new_sol) < self._calculate_total_cost(best_solution)):
                                best_solution = new_sol
                                improved = True
                                break
                        
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
                    
        return best_solution if best_solution != solution else None
    
    def _find_route_containing_node(self, node_idx: int, routes: List[List[int]]) -> int:
        """Find route index containing given node"""
        for route_idx, route in enumerate(routes):
            if node_idx in route:
                return route_idx
        return -1
    
    def _get_pickup_delivery_pairs_in_route(self, route: List[int]) -> List[Tuple[int, int]]:
        """Get pickup-delivery pairs found in route"""
        pairs = []
        pickup_nodes = []
        
        for node_idx in route:
            node = self.instance.nodes[node_idx]
            if node.is_pickup():
                pickup_nodes.append(node_idx)
                
        for pickup_idx in pickup_nodes:
            pickup_node = self.instance.nodes[pickup_idx]
            if pickup_node.pair in route:
                pairs.append((pickup_idx, pickup_node.pair))
                
        return pairs
    
    def _get_node_position(self, route: List[int], node_idx: int) -> int:
        """Get position of node in route"""
        return route.index(node_idx) if node_idx in route else -1
    
    def _merge_pairs_into_route(self, base_route: List[int], pairs: List[Tuple[int, int]]) -> List[int]:
        """Merge pickup-delivery pairs into a route maintaining precedence"""
        result_route = base_route[:]
        
        for pickup_idx, delivery_idx in pairs:
            pickup_pos = self._find_best_insertion_position(result_route, pickup_idx, True)
            result_route.insert(pickup_pos, pickup_idx)
            
            delivery_pos = self._find_best_delivery_position(result_route, pickup_pos, delivery_idx)
            result_route.insert(delivery_pos, delivery_idx)
            
        return result_route
    
    def _find_best_insertion_position(self, route: List[int], node_idx: int, is_pickup: bool) -> int:
        """Find best position to insert node in route"""
        node = self.instance.nodes[node_idx]
        best_pos = 0
        best_cost = float('inf')
        
        for pos in range(len(route) + 1):
            temp_route = route[:pos] + [node_idx] + route[pos:]
            
            if self._is_feasible_route(temp_route, check_pairs=is_pickup):
                cost = self._calculate_route_cost(temp_route) - self._calculate_route_cost(route)
                if cost < best_cost:
                    best_cost = cost
                    best_pos = pos
                    
        return best_pos
    
    def _is_feasible_route(self, route: List[int], check_pairs: bool = True) -> bool:
        """Check if route satisfies all constraints"""
        if not route:
            return True
            
        time = 0
        load = 0
        visited_pickups = set()
        
        prev_node = 0  # Start from depot
        
        for node_id in route:
            node = self.instance.nodes[node_id]
            
            # Update travel time and check time window
            time += self.instance.get_travel_time(prev_node, node_id)
            arrival_time = max(time, node.etw)
            
            if arrival_time > node.ltw:
                return False
                
            # Check pickup-delivery precedence
            if check_pairs and node.is_delivery():
                pickup_idx = node.pair
                if pickup_idx not in visited_pickups:
                    return False
                    
            # Check capacity constraint
            load += node.dem
            if load > self.instance.capacity or load < 0:
                return False
                
            if node.is_pickup():
                visited_pickups.add(node_id)
                
            time = arrival_time + node.dur
            prev_node = node_id
            
        return True
    
    def _calculate_route_cost(self, route: List[int]) -> int:
        """Calculate total travel cost for a route"""
        if len(route) <= 1:
            return 0
            
        total_cost = 0
        prev_node = 0  # depot
        
        for node_id in route:
            total_cost += self.instance.get_travel_time(prev_node, node_id)
            prev_node = node_id
            
        # Return to depot
        if route:
            total_cost += self.instance.get_travel_time(route[-1], 0)
            
        return total_cost
    
    def _calculate_total_cost(self, solution: Solution) -> int:
        """Calculate total cost for entire solution"""
        total_cost = 0
        for route in solution.routes:
            total_cost += self._calculate_route_cost(route)
        return total_cost
    
    def _is_valid_solution(self, solution: Solution) -> bool:
        """Check if entire solution is valid"""
        # Check all routes are feasible
        for route in solution.routes:
            if not self._is_feasible_route(route):
                return False
                
        # Check all nodes are visited exactly once
        all_nodes = set()
        for route in solution.routes:
            for node_id in route:
                if node_id in all_nodes:
                    return False  # Node visited twice
                all_nodes.add(node_id)
                
        # Check all required nodes are visited
        required_nodes = set(node.idx for node in self.instance.nodes[1:])  # Exclude depot
        visited_nodes = all_nodes - {0}  # Exclude depot
        
        return required_nodes == visited_nodes
    
    def multi_route_improvement(self, solution: Solution) -> Optional[Solution]:
        """Apply comprehensive local search to improve solution"""
        improved_solution = copy.deepcopy(solution)
        
        # Apply OR-opt improvements
        or_opt_result = self.or_opt_pickup_delivery(improved_solution)
        if or_opt_result:
            improved_solution = or_opt_result
            
        # Apply 2-opt to each route
        for route_idx, route in enumerate(improved_solution.routes):
            improved_route = self.two_opt_route(route)
            improved_solution.routes[route_idx] = improved_route
            
        return improved_solution if improved_solution != solution else None


if __name__ == "__main__":
    print("Local search operators implemented")
    print("Available methods:")
    print("- relocate_pickup_delivery_pair")
    print("- exchange_pickup_delivery_pairs")
    print("- two_opt_route")
    print("- or_opt_pickup_delivery")
    print("- multi_route_improvement")
