"""
Route Elimination - Direct vehicle minimization
================================================
Systematically tries to eliminate routes by reinserting their requests
into remaining routes. This is a "vehicles-first" optimization.
"""

from typing import List, Tuple, Optional
from data_loader import Instance, Solution
import random


class RouteElimination:
    """
    Route Elimination strategy for vehicle minimization
    
    Strategy:
    1. Select smallest route (fewest requests)
    2. Remove all requests from that route
    3. Try to reinsert them into remaining routes (using regret-k)
    4. If successful → reduced 1 vehicle
    5. Repeat until no more routes can be eliminated
    """
    
    def __init__(self, instance: Instance):
        self.instance = instance
        
    def eliminate_routes(self, solution: Solution, max_iterations: int = 50, 
                        max_time: float = 30.0) -> Tuple[Solution, int]:
        """
        Try to eliminate routes from solution
        
        Args:
            solution: Current solution
            max_iterations: Maximum elimination attempts
            max_time: Time limit in seconds
            
        Returns:
            (improved_solution, num_eliminated)
        """
        import time
        from feasibility_validator import validate_solution
        
        start_time = time.time()
        eliminated_count = 0
        
        for iteration in range(max_iterations):
            if time.time() - start_time > max_time:
                break
            
            # Get non-empty routes
            active_routes = [(i, route) for i, route in enumerate(solution.routes) if route]
            
            if len(active_routes) <= 1:
                break  # Can't eliminate if only 1 route left
            
            # Sort by number of requests (smallest first)
            active_routes.sort(key=lambda x: len(x[1]))
            
            # Try to eliminate smallest route
            route_idx, route_to_eliminate = active_routes[0]
            
            # Get all requests from this route (pickup-delivery pairs)
            requests = self._extract_requests(route_to_eliminate)
            
            if not requests:
                # Empty route, just remove it
                solution.routes[route_idx] = []
                eliminated_count += 1
                continue
            
            # Try to reinsert all requests into other routes
            candidate_solution = self._copy_solution(solution)
            candidate_solution.routes[route_idx] = []  # Remove the route
            
            # Reinsert requests using regret-k
            success = self._reinsert_requests(candidate_solution, requests)
            
            if success:
                # Check feasibility
                is_feasible, _ = validate_solution(candidate_solution, self.instance)
                
                if is_feasible:
                    # Success! Accept the elimination
                    solution = candidate_solution
                    eliminated_count += 1
                    # print(f"  [RouteElim] Eliminated route {route_idx}, now {len([r for r in solution.routes if r])} vehicles")
                else:
                    # Infeasible, can't eliminate this route
                    break
            else:
                # Couldn't reinsert, can't eliminate
                break
        
        return solution, eliminated_count
    
    def _extract_requests(self, route: List[int]) -> List[Tuple[int, int]]:
        """Extract pickup-delivery pairs from route"""
        requests = []
        visited_pickups = set()
        
        for node_id in route:
            node = self.instance.nodes[node_id]
            
            if node.dem > 0:  # Pickup
                delivery_id = node.pair
                requests.append((node_id, delivery_id))
                visited_pickups.add(node_id)
        
        return requests
    
    def _reinsert_requests(self, solution: Solution, requests: List[Tuple[int, int]]) -> bool:
        """
        Try to reinsert all requests into solution using regret-k insertion
        
        Returns:
            True if all requests successfully inserted
        """
        # Shuffle requests for diversity
        requests = list(requests)
        random.shuffle(requests)
        
        for pickup_id, delivery_id in requests:
            # Find best insertion using regret-2
            best_route_idx = None
            best_positions = None
            best_cost = float('inf')
            second_best_cost = float('inf')
            
            # Try inserting into each existing route
            for route_idx, route in enumerate(solution.routes):
                if not route:
                    continue
                
                # Find best position for this request in this route
                positions, cost = self._find_best_insertion(route, pickup_id, delivery_id)
                
                if cost < best_cost:
                    second_best_cost = best_cost
                    best_cost = cost
                    best_route_idx = route_idx
                    best_positions = positions
                elif cost < second_best_cost:
                    second_best_cost = cost
            
            # Calculate regret and insert
            if best_route_idx is not None:
                regret = second_best_cost - best_cost
                # Insert at best position
                pickup_pos, delivery_pos = best_positions
                route = solution.routes[best_route_idx]
                
                # Insert delivery first (at higher index)
                route.insert(delivery_pos, delivery_id)
                # Then pickup
                route.insert(pickup_pos, pickup_id)
            else:
                # Couldn't insert into any existing route
                return False
        
        return True
    
    def _find_best_insertion(self, route: List[int], pickup_id: int, delivery_id: int) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Find best position to insert pickup-delivery pair in route
        
        Returns:
            ((pickup_pos, delivery_pos), cost_increase)
        """
        best_positions = None
        best_cost = float('inf')
        
        # Try all valid positions
        for pickup_pos in range(len(route) + 1):
            for delivery_pos in range(pickup_pos + 1, len(route) + 2):
                # Create temp route
                temp_route = route.copy()
                temp_route.insert(delivery_pos, delivery_id)
                temp_route.insert(pickup_pos, pickup_id)
                
                # Check basic feasibility and calculate cost
                if self._is_route_feasible_quick(temp_route):
                    cost = self._calculate_route_cost(temp_route)
                    
                    if cost < best_cost:
                        best_cost = cost
                        best_positions = (pickup_pos, delivery_pos)
        
        if best_positions is None:
            return None, float('inf')
        
        return best_positions, best_cost
    
    def _is_route_feasible_quick(self, route: List[int]) -> bool:
        """Quick feasibility check (pickup before delivery, capacity, time windows)"""
        if not route:
            return True
        
        # Check pickup before delivery
        visited = set()
        for node_id in route:
            node = self.instance.nodes[node_id]
            if node.dem < 0:  # Delivery
                if node.pair not in visited:
                    return False
            visited.add(node_id)
        
        # Check capacity and time windows
        depot = self.instance.nodes[0]
        current_time = depot.etw
        current_load = 0
        current_location = 0
        
        for node_id in route:
            node = self.instance.nodes[node_id]
            
            # Travel
            travel_time = self.instance.get_travel_time(current_location, node_id)
            arrival_time = current_time + travel_time
            service_start = max(arrival_time, node.etw)
            
            # Check time window
            if service_start > node.ltw:
                return False
            
            # Check capacity
            current_load += node.dem
            if current_load > self.instance.capacity:
                return False
            
            current_time = service_start + node.dur
            current_location = node_id
        
        # Return to depot
        return_time = current_time + self.instance.get_travel_time(current_location, 0)
        return return_time <= depot.ltw
    
    def _calculate_route_cost(self, route: List[int]) -> float:
        """Calculate total distance of route"""
        if not route:
            return 0
        
        cost = 0
        current = 0  # Depot
        
        for node_id in route:
            cost += self.instance.get_travel_time(current, node_id)
            current = node_id
        
        cost += self.instance.get_travel_time(current, 0)  # Return to depot
        
        return cost
    
    def _copy_solution(self, solution: Solution) -> Solution:
        """Deep copy solution"""
        new_solution = Solution()
        new_solution.routes = [route.copy() for route in solution.routes]
        new_solution.inst_name = solution.inst_name
        return new_solution


if __name__ == "__main__":
    # Quick test
    from data_loader import Instance
    from clarke_wright_pdptw import ClarkeWrightPDPTW
    from feasibility_validator import validate_solution
    
    print("="*80)
    print("TESTING ROUTE ELIMINATION")
    print("="*80)
    
    instance = Instance()
    instance.read_from_file("../instances/pdp_100/lc101.txt")
    
    # Create initial solution with Clarke-Wright
    cw = ClarkeWrightPDPTW(instance)
    routes = cw.solve(max_time=30)
    
    solution = Solution()
    solution.routes = routes
    solution.inst_name = "lc101"
    
    initial_vehicles = len([r for r in routes if r])
    print(f"\nInitial: {initial_vehicles} vehicles")
    
    # Try route elimination
    re = RouteElimination(instance)
    improved_solution, eliminated = re.eliminate_routes(solution, max_iterations=50, max_time=30)
    
    final_vehicles = len([r for r in improved_solution.routes if r])
    is_feasible, _ = validate_solution(improved_solution, instance)
    
    print(f"After elimination: {final_vehicles} vehicles (eliminated {eliminated})")
    print(f"Feasible: {is_feasible}")
    print("="*80)
