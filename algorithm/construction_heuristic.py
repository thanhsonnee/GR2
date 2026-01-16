"""
Construction heuristic algorithms for PDPTW
Implements simple greedy heuristics to build initial solutions
"""

import random
from typing import List, Tuple, Set, Optional
from data_loader import Instance, Node
from solution_encoder import SolutionEncoder
from clarke_wright_pdptw import ClarkeWrightPDPTW


class ConstructionHeuristic:
    """Base class for construction heuristics"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        
    def solve(self) -> List[List[int]]:
        """Solve the instance and return list of routes"""
        raise NotImplementedError
        
    def calculate_insertion_cost(self, pickup_node: Node, delivery_node: Node, 
                                route: List[int], position: int) -> int:
        """Calculate cost of inserting pickup-delivery pair into route at given position"""
        if position > len(route):
            position = len(route)
            
        # Add pickup first, then delivery
        temp_route = route[:position] + [pickup_node.idx] + route[position:]
        
        # Find best position for delivery node
        best_cost = float('inf')
        best_delivery_pos = position + 1
        
        for j in range(position + 1, len(temp_route) + 1):
            # Check if delivery can be inserted here (after pickup, before max capacity)
            delivery_possible = True
            load_after_pickup = self.node_demand_at_position(temp_route, position)
            
            # Check constraints for pickup insertion
            travel_time = self.calculate_total_time(temp_route[:position])
            travel_time += self.instance.get_travel_time(temp_route[position-1] if position > 0 else 0, pickup_node.idx)
            
            if travel_time > pickup_node.ltw:
                delivery_possible = False
                
            travel_time = max(travel_time, pickup_node.etw) + pickup_node.dur
            travel_time += self.instance.get_travel_time(pickup_node.idx, self.instance.nodes[temp_route[j-1] if j <= len(temp_route) else temp_route[-1]].idx)
            
            if delivery_possible:
                # Insert delivery at position j
                temp_route_with_delivery = temp_route[:j] + [delivery_node.idx] + temp_route[j:]
                cost = self.calculate_total_time(temp_route_with_delivery) - self.calculate_total_time(route)
                if cost < best_cost:
                    best_cost = cost
                    best_delivery_pos = j
                    
        return best_cost
        
    def node_demand_at_position(self, route: List[int], position: int) -> int:
        """Calculate vehicle load up to given position in route"""
        load = 0
        for i in range(position):
            node_id = route[i]
            node = self.instance.nodes[node_id]
            load += node.dem
        return load
        
    def calculate_total_time(self, route: List[int]) -> int:
        """Calculate total travel time for a route"""
        if not route:
            return 0
            
        total_time = 0
        prev_node = 0  # START FROM DEPOT!
        
        for node_id in route:
            # Travel time from previous node
            total_time += self.instance.get_travel_time(prev_node, node_id)
            
            # Wait if arrived too early
            node = self.instance.nodes[node_id]
            total_time = max(total_time, node.etw)
            
            # Add service time
            total_time += node.dur
            prev_node = node_id
        
        # Return to depot
        total_time += self.instance.get_travel_time(prev_node, 0)
            
        return total_time
        
    def is_feasible_insertion(self, pickup_node: Node, delivery_node: Node, 
                            route: List[int], pickup_pos: int) -> bool:
        """Check if inserting pickup-delivery pair at position is feasible"""
        # Create temporary route with pickup inserted
        temp_route = route[:pickup_pos] + [pickup_node.idx] + route[pickup_pos:]
        
        # Try all possible delivery positions after pickup
        for delivery_pos in range(pickup_pos + 1, len(temp_route) + 1):
            test_route = temp_route[:delivery_pos] + [delivery_node.idx] + temp_route[delivery_pos:]
            
            # Check if this complete route is feasible
            if self.is_feasible_route(test_route):
                return True
        
        return False


class GreedyInsertion(ConstructionHeuristic):
    """Greedy insertion heuristic"""
    
    def solve(self) -> List[List[int]]:
        """Solve using greedy algorithm"""
        # Initialize with empty routes
        routes = []
        unvisited_pairs = self.instance.get_pickup_delivery_pairs()
        
        while unvisited_pairs:
            best_cost = float('inf')
            best_pair = None
            best_route_idx = -1
            best_position = -1
            
            # Try all unvisited pickup-delivery pairs
            for pickup_idx, delivery_idx in unvisited_pairs:
                pickup_node = self.instance.nodes[pickup_idx]
                delivery_node = self.instance.nodes[delivery_idx]
                
                # Try inserting into existing routes
                for route_idx, route in enumerate(routes):
                    for pos in range(len(route) + 1):
                        if self.is_feasible_insertion(pickup_node, delivery_node, route, pos):
                            cost = self.calculate_insertion_cost(pickup_node, delivery_node, route, pos)
                            if cost < best_cost:
                                best_cost = cost
                                best_pair = (pickup_idx, delivery_idx)
                                best_route_idx = route_idx
                                best_position = pos
                
                # Try creating new route
                new_route_cost = self.create_new_route_cost(pickup_node, delivery_node)
                
                # Set realistic minimum vehicles based on instance size
                min_vehicles_needed = max(3, len(self.instance.get_pickup_delivery_pairs()) // 12)  # At least 1 vehicle per 12 pairs
                max_vehicles_allowed = len(self.instance.get_pickup_delivery_pairs()) // 3  # At most 1 vehicle per 3 pairs
                
                # Strongly encourage creating new routes when we have too few vehicles
                if len(routes) < min_vehicles_needed:
                    new_route_cost *= 0.5  # Heavy penalty to force more vehicles
                elif len(routes) < min_vehicles_needed * 1.5:
                    new_route_cost *= 0.8  # Medium penalty
                
                if new_route_cost < best_cost:
                    best_cost = new_route_cost
                    best_pair = (pickup_idx, delivery_idx)
                    best_route_idx = -1  # New route
                    best_position = 0
            
            # Insert best pair
            if best_route_idx == -1:
                # Create new route
                pickup_idx, delivery_idx = best_pair
                pickup_node = self.instance.nodes[pickup_idx]
                delivery_node = self.instance.nodes[delivery_idx]
                routes.append([pickup_node.idx, delivery_node.idx])
            else:
                # Insert into existing route
                pickup_idx, delivery_idx = best_pair
                pickup_node = self.instance.nodes[pickup_idx]
                delivery_node = self.instance.nodes[delivery_idx]
                
                # Find best delivery position
                route = routes[best_route_idx]
                
                # IMPORTANT: Insert pickup FIRST into temp route!
                temp_route_with_pickup = route[:best_position] + [pickup_node.idx] + route[best_position:]
                best_delivery_pos = best_position + 1
                
                # Now find where to insert delivery (must be AFTER pickup)
                for j in range(best_position + 1, len(temp_route_with_pickup) + 1):
                    temp_route = temp_route_with_pickup[:j] + [delivery_node.idx] + temp_route_with_pickup[j:]
                    if self.is_feasible_route(temp_route):
                        best_delivery_pos = j
                        break
                        
                # Insert pickup and delivery (pickup first!)
                routes[best_route_idx].insert(best_position, pickup_node.idx)
                routes[best_route_idx].insert(best_delivery_pos, delivery_node.idx)  # NO +1!
            
            # Remove inserted pair
            unvisited_pairs.remove(best_pair)
        
        return routes
        
    def create_new_route_cost(self, pickup_node: Node, delivery_node: Node) -> int:
        """Calculate cost of creating new route for pickup-delivery pair"""
        # Depots are usually at index 0
        depot_cost = (self.instance.get_travel_time(0, pickup_node.idx) + 
                     self.instance.get_travel_time(pickup_node.idx, delivery_node.idx) +
                     self.instance.get_travel_time(delivery_node.idx, 0))
        return depot_cost
        
    def is_feasible_route(self, route: List[int]) -> bool:
        """Check if route satisfies all constraints"""
        if not route:
            return True
            
        time = 0
        load = 0
        visited_pickups = set()
        
        prev_node = 0  # Start from depot
        for node_id in route:
            node = self.instance.nodes[node_id]
            
            # Update travel time
            travel_time = self.instance.get_travel_time(prev_node, node_id)
            time += travel_time
            
            # Wait until time window opens
            arrival_time = max(time, node.etw)
            
            # Check time window constraint
            if arrival_time > node.ltw:
                return False
                
            # Check pickup-delivery precedence
            if node.is_delivery():
                pickup_idx = node.pair
                if pickup_idx not in visited_pickups:
                    return False
                    
            # Update load and check capacity
            load += node.dem
            if load > self.instance.capacity or load < 0:
                return False
                
            # Mark pickup as visited
            if node.is_pickup():
                visited_pickups.add(node_id)
                
            # Update time after service
            time = arrival_time + node.dur
            prev_node = node_id
            
        # Check return to depot time window
        return_time = time + self.instance.get_travel_time(prev_node, 0)
        depot_node = self.instance.nodes[0]
        if return_time > depot_node.ltw:
            return False
            
        return True


class NearestNeighbor(ConstructionHeuristic):
    """Nearest neighbor heuristic adapted for PDPTW"""
    
    def solve(self) -> List[List[int]]:
        """Solve using nearest neighbor approach"""
        routes = []
        unvisited_pairs = self.instance.get_pickup_delivery_pairs()
        
        while unvisited_pairs:
            # Start new route from depot
            route = []
            current_node = 0  # depot
            time = 0
            load = 0
            
            while unvisited_pairs:
                # Find nearest feasible pickup
                best_pair = None
                best_cost = float('inf')
                
                for pickup_idx, delivery_idx in unvisited_pairs:
                    pickup_node = self.instance.nodes[pickup_idx]
                    
                    # Check if pickup can be reached
                    pickup_arrival = time + self.instance.get_travel_time(current_node, pickup_idx)
                    pickup_start = max(pickup_arrival, pickup_node.etw)
                    
                    if pickup_start <= pickup_node.ltw and load + pickup_node.dem <= self.instance.capacity:
                        cost = self.instance.get_travel_time(current_node, pickup_idx)
                        if cost < best_cost:
                            best_cost = cost
                            best_pair = (pickup_idx, delivery_idx)
                
                if best_pair is None:
                    break  # No feasible pickup found, end route
                    
                # Add pickup to route
                pickup_idx, delivery_idx = best_pair
                pickup_node = self.instance.nodes[pickup_idx]
                route.append(pickup_idx)
                
                # Update time and load
                time += self.instance.get_travel_time(current_node, pickup_idx)
                time = max(time, pickup_node.etw) + pickup_node.dur
                load += pickup_node.dem
                current_node = pickup_idx
                
                # Add delivery as soon as possible
                delivery_node = self.instance.nodes[delivery_idx]
                time += self.instance.get_travel_time(current_node, delivery_idx)
                time = max(time, delivery_node.etw) + delivery_node.dur
                load += delivery_node.dem
                
                route.append(delivery_idx)
                current_node = delivery_idx
                
                # Remove from unvisited
                unvisited_pairs.remove(best_pair)
            
            if route:
                routes.append(route)
                
        return routes


# Utility functions for construction algorithms
def create_solution_from_routes(routes: List[List[int]], instance: Instance, 
                               authors: str = "Construction Heuristic"):
    """Create Solution object from routes"""
    return SolutionEncoder.create_solution_from_routes(routes, instance.name, authors)


if __name__ == "__main__":
    print("Construction heuristic algorithms implemented")
    print("Available algorithms:")
    print("- GreedyInsertion")
    print("- NearestNeighbor")
