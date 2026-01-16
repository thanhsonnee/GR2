"""
Clarke-Wright Savings Algorithm for PDPTW
Better construction heuristic than GreedyInsertion
Ensures feasibility from the start
"""

import random
from typing import List, Tuple, Dict
from data_loader import Instance, Solution


class ClarkeWrightSavings:
    """
    Clarke-Wright Savings algorithm adapted for PDPTW
    Creates feasible initial solutions by:
    1. Starting with individual routes for each request
    2. Merging routes based on savings
    3. Checking feasibility at every step
    """
    
    def __init__(self, instance: Instance):
        self.instance = instance
        self.depot = 0
        
    def solve(self) -> List[List[int]]:
        """Generate initial solution using Clarke-Wright Savings"""
        print("Clarke-Wright: Building initial solution...")
        
        # Step 1: Create individual routes for each pickup-delivery pair
        routes = self._create_individual_routes()
        print(f"Clarke-Wright: Started with {len(routes)} individual routes")
        
        # Step 2: Calculate savings for all pairs of routes
        savings = self._calculate_savings(routes)
        print(f"Clarke-Wright: Calculated {len(savings)} potential merges")
        
        # Step 3: Merge routes based on savings (highest first)
        merged_count = 0
        for (i, j, saving) in sorted(savings, key=lambda x: -x[2]):
            if i >= len(routes) or j >= len(routes):
                continue
                
            if self._can_merge_routes(routes[i], routes[j]):
                routes[i] = self._merge_routes(routes[i], routes[j])
                routes.pop(j)
                merged_count += 1
                
                if merged_count % 10 == 0:
                    print(f"Clarke-Wright: Merged {merged_count} routes, current count: {len(routes)}")
        
        print(f"Clarke-Wright: Final solution with {len(routes)} routes")
        return routes
    
    def _create_individual_routes(self) -> List[List[int]]:
        """Create one route per pickup-delivery pair"""
        routes = []
        pairs = self.instance.get_pickup_delivery_pairs()
        
        for pickup, delivery in pairs:
            # Route: depot -> pickup -> delivery -> depot
            # We store without explicit depots (added later)
            route = [pickup, delivery]
            routes.append(route)
        
        return routes
    
    def _calculate_savings(self, routes: List[List[int]]) -> List[Tuple[int, int, float]]:
        """
        Calculate savings for merging each pair of routes
        Savings(i,j) = distance(i, depot) + distance(depot, j) - distance(i, j)
        """
        savings = []
        
        for i in range(len(routes)):
            for j in range(i + 1, len(routes)):
                # Get last node of route i and first node of route j
                last_i = routes[i][-1]
                first_j = routes[j][0]
                
                # Calculate saving
                saving = (self.instance.times[last_i][self.depot] +
                         self.instance.times[self.depot][first_j] -
                         self.instance.times[last_i][first_j])
                
                if saving > 0:  # Only positive savings
                    savings.append((i, j, saving))
        
        return savings
    
    def _can_merge_routes(self, route1: List[int], route2: List[int]) -> bool:
        """Check if two routes can be merged while maintaining feasibility"""
        # Create merged route
        merged = route1 + route2
        
        # Check 0: Route length limit (prevent merging into 1 mega-route)
        # For n100: limit route to ~15-20 customers max
        if len(merged) > 20:
            return False
        
        # Check 1: Capacity constraint
        total_load = 0
        max_load = 0
        for node in merged:
            demand = self.instance.nodes[node].dem
            total_load += demand
            max_load = max(max_load, total_load)
            if max_load > self.instance.capacity or total_load < 0:
                return False
        
        # Check 2: Time windows (basic check)
        if not self._check_time_windows_simple(merged):
            return False
        
        # Check 3: Pairing constraint (pickup before delivery)
        if not self._check_pairing(merged):
            return False
        
        return True
    
    def _check_pairing(self, route: List[int]) -> bool:
        """
        Check if all pickups come before their deliveries
        For PDPTW: node i is pickup, node i+n is delivery
        """
        n = len(self.instance.nodes) // 2
        visited_pickups = set()
        
        for node in route:
            if node == 0:  # Skip depot
                continue
                
            if node <= n:  # Pickup node
                visited_pickups.add(node)
            else:  # Delivery node
                pickup = node - n
                if pickup not in visited_pickups:
                    return False  # Delivery before pickup!
        
        return True
    
    def _check_time_windows_simple(self, route: List[int]) -> bool:
        """
        Simple time window check - estimate if route is feasible time-wise
        """
        # Calculate total time needed
        current_time = 0
        prev_node = 0  # depot
        
        for node in route:
            # Travel time
            current_time += self.instance.times[prev_node][node]
            
            # Wait if arrived too early
            earliest = self.instance.nodes[node].etw
            if current_time < earliest:
                current_time = earliest
            
            # Check if arrived too late
            latest = self.instance.nodes[node].ltw
            if current_time > latest:
                return False  # Violated time window!
            
            # Service time
            current_time += self.instance.nodes[node].dur
            
            prev_node = node
        
        # Return to depot
        current_time += self.instance.times[prev_node][0]
        
        # Check time horizon
        if current_time > self.instance.time_window:
            return False
        
        return True
    
    def _merge_routes(self, route1: List[int], route2: List[int]) -> List[int]:
        """Merge two routes: route1 -> route2"""
        return route1 + route2


class ImprovedGreedyInsertion:
    """
    Improved Greedy Insertion with better feasibility checking
    Fallback if Clarke-Wright doesn't work well
    """
    
    def __init__(self, instance: Instance):
        self.instance = instance
        
    def solve(self) -> List[List[int]]:
        """Build solution by inserting requests one by one"""
        routes = []
        unserved = list(self.instance.get_pickup_delivery_pairs())
        
        # Sort by early time window
        unserved.sort(key=lambda p: self.instance.nodes[p[0]].etw)
        
        while unserved:
            # Try to insert into existing routes
            inserted = False
            pickup, delivery = unserved[0]
            
            for route in routes:
                if self._can_insert(route, pickup, delivery):
                    best_pos = self._find_best_position(route, pickup, delivery)
                    if best_pos is not None:
                        route.insert(best_pos[0], pickup)
                        route.insert(best_pos[1], delivery)
                        unserved.pop(0)
                        inserted = True
                        break
            
            # Create new route if couldn't insert
            if not inserted:
                routes.append([pickup, delivery])
                unserved.pop(0)
        
        return routes
    
    def _can_insert(self, route: List[int], pickup: int, delivery: int) -> bool:
        """Check if pickup-delivery pair can be inserted into route"""
        # Basic capacity check
        pickup_demand = self.instance.nodes[pickup].dem
        delivery_demand = self.instance.nodes[delivery].dem
        
        current_load = sum(self.instance.nodes[n].dem for n in route)
        max_load = current_load + pickup_demand  # Peak load
        
        return max_load <= self.instance.capacity
    
    def _find_best_position(self, route: List[int], pickup: int, delivery: int) -> Tuple[int, int]:
        """Find best position to insert pickup and delivery"""
        best_cost = float('inf')
        best_pos = None
        
        # Try all valid positions (pickup before delivery)
        for i in range(len(route) + 1):
            for j in range(i, len(route) + 2):
                # Calculate insertion cost
                cost = self._insertion_cost(route, pickup, delivery, i, j)
                if cost < best_cost:
                    best_cost = cost
                    best_pos = (i, j)
        
        return best_pos
    
    def _insertion_cost(self, route: List[int], pickup: int, delivery: int, 
                       pos_pickup: int, pos_delivery: int) -> float:
        """Calculate cost of inserting at given positions"""
        # Simplified: just distance increase
        test_route = route[:]
        test_route.insert(pos_pickup, pickup)
        test_route.insert(pos_delivery, delivery)
        
        # Calculate total distance
        total_dist = 0
        prev = 0  # depot
        for node in test_route:
            total_dist += self.instance.times[prev][node]
            prev = node
        total_dist += self.instance.times[prev][0]  # back to depot
        
        return total_dist


# Factory function to choose best construction
def get_best_construction(instance: Instance) -> List[List[int]]:
    """
    Try multiple construction heuristics and return the most realistic one
    Prioritize: feasibility > reasonable vehicle count > low cost
    """
    print("\n" + "="*60)
    print("CONSTRUCTING INITIAL SOLUTION")
    print("="*60)
    
    candidates = []
    
    # Try 1: Clarke-Wright Savings
    try:
        print("\nMethod 1: Clarke-Wright Savings...")
        cw = ClarkeWrightSavings(instance)
        cw_routes = cw.solve()
        candidates.append(('Clarke-Wright', cw_routes, len(cw_routes)))
        print(f"  -> Success: {len(cw_routes)} vehicles")
    except Exception as e:
        print(f"  -> Failed: {e}")
    
    # Try 2: Original Greedy (more conservative)
    try:
        print("\nMethod 2: Original Greedy Insertion...")
        from construction_heuristic import GreedyInsertion
        greedy = GreedyInsertion(instance)
        greedy_routes = greedy.solve()
        candidates.append(('Greedy', greedy_routes, len(greedy_routes)))
        print(f"  -> Success: {len(greedy_routes)} vehicles")
    except Exception as e:
        print(f"  -> Failed: {e}")
    
    # Choose best: prefer solution with realistic vehicle count (5-15 for n100)
    # Expected: ~10-15 vehicles for 50 pairs
    if not candidates:
        raise Exception("All construction methods failed!")
    
    # Sort by how close to target range (10-15 vehicles)
    target_vehicles = max(5, len(instance.get_pickup_delivery_pairs()) // 5)
    
    def score_solution(method, routes, num_vehicles):
        # Prefer solutions in range [target/2, target*2]
        if num_vehicles < 2:
            return 9999  # Too few = infeasible
        elif num_vehicles <= target_vehicles * 1.5:
            return abs(num_vehicles - target_vehicles)  # Prefer close to target
        else:
            return num_vehicles + 100  # Penalize too many vehicles
    
    candidates.sort(key=lambda x: score_solution(*x))
    
    best_method, best_routes, best_vehicles = candidates[0]
    
    print(f"\nSelected: {best_method} with {best_vehicles} vehicles")
    print(f"(Target range: {target_vehicles//2}-{target_vehicles*2} vehicles)")
    print("="*60)
    return best_routes

