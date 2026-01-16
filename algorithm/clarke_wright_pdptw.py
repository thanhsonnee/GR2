"""
Clarke-Wright Savings Algorithm for PDPTW
==========================================
Classical heuristic that builds good initial solutions
"""

from typing import List, Tuple
from data_loader import Instance, Node, Solution
import time
import sys

# Fix encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class ClarkeWrightPDPTW:
    """Clarke-Wright Savings Algorithm adapted for PDPTW"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        self.depot = instance.nodes[0]  # Depot is always node 0
        
    def solve(self, max_time: float = 60.0) -> List[List[int]]:
        """
        Build initial solution using Clarke-Wright savings algorithm
        
        Returns:
            List of routes (each route is list of node indices)
        """
        start_time = time.time()
        
        # Step 1: Create initial solution - one route per request pair
        routes = self._create_initial_routes()
        print(f"[CW] Initial: {len(routes)} vehicles")
        
        # Step 2: Calculate savings for all route pairs
        savings = self._calculate_savings(routes)
        if not savings:
            return routes
        
        # Sort by savings (descending)
        savings.sort(key=lambda x: x[2], reverse=True)
        print(f"[CW] Calculated {len(savings)} potential merges")
        
        # Step 3: Merge routes greedily based on savings
        merged_count = 0
        for route_i, route_j, saving in savings:
            if time.time() - start_time > max_time:
                break
            
            # Check if routes still valid
            if route_i >= len(routes) or route_j >= len(routes):
                continue
            if not routes[route_i] or not routes[route_j]:
                continue
            
            # Try merge
            if self._try_merge_routes(routes, route_i, route_j):
                merged_count += 1
                if merged_count % 10 == 0:
                    active = sum(1 for r in routes if r)
                    print(f"[CW] Merged {merged_count} routes -> {active} vehicles")
        
        # Clean up empty routes
        routes = [r for r in routes if r]
        print(f"[CW] Final: {len(routes)} vehicles (merged {merged_count})")
        
        return routes
    
    def _create_initial_routes(self) -> List[List[int]]:
        """Create one route per request pair"""
        routes = []
        
        # Get pickup nodes (excluding depot)
        pickups = [n for n in self.instance.nodes if n.dem > 0]
        
        for pickup in pickups:
            delivery_idx = pickup.pair
            # Create route: [pickup_idx, delivery_idx]
            route = [pickup.idx, delivery_idx]
            routes.append(route)
        
        return routes
    
    def _calculate_savings(self, routes: List[List[int]]) -> List[Tuple[int, int, float]]:
        """
        Calculate savings s(i,j) = d(0,i) + d(0,j) - d(i,j)
        where 0 is depot, i is last node of route_i, j is first node of route_j
        """
        savings = []
        
        for i in range(len(routes)):
            if not routes[i]:
                continue
            i_last = routes[i][-1]  # Delivery node
            
            for j in range(i + 1, len(routes)):
                if not routes[j]:
                    continue
                j_first = routes[j][0]  # Pickup node
                
                # Calculate saving
                d_0_i = self.instance.get_travel_time(0, i_last)
                d_0_j = self.instance.get_travel_time(0, j_first)
                d_i_j = self.instance.get_travel_time(i_last, j_first)
                
                saving = d_0_i + d_0_j - d_i_j
                
                if saving > 0:
                    savings.append((i, j, saving))
        
        return savings
    
    def _try_merge_routes(self, routes: List[List[int]], i: int, j: int) -> bool:
        """Try to merge route_j into route_i"""
        merged = routes[i] + routes[j]
        
        # Check feasibility
        if not self._is_route_feasible(merged):
            return False
        
        # Merge successful
        routes[i] = merged
        routes[j] = []
        return True
    
    def _is_route_feasible(self, route: List[int]) -> bool:
        """Check if route satisfies PDPTW constraints"""
        if not route:
            return True
        
        # Check 1: Pickup before delivery
        visited = set()
        for node_idx in route:
            node = self.instance.nodes[node_idx]
            if node.dem < 0:  # Delivery
                # Check if pickup was visited
                if node.pair not in visited:
                    return False
            visited.add(node_idx)
        
        # Check 2: Time windows and capacity
        current_time = self.depot.etw
        current_load = 0
        current_location = 0  # Depot
        
        for node_idx in route:
            node = self.instance.nodes[node_idx]
            
            # Travel
            travel_time = self.instance.get_travel_time(current_location, node_idx)
            arrival_time = current_time + travel_time
            
            # Wait if early
            service_start = max(arrival_time, node.etw)
            
            # Check time window
            if service_start > node.ltw:
                return False
            
            # Update load
            current_load += node.dem
            
            # Check capacity
            if current_load > self.instance.capacity:
                return False
            
            # Update state
            current_time = service_start + node.dur
            current_location = node_idx
        
        # Return to depot
        return_travel = self.instance.get_travel_time(current_location, 0)
        return_time = current_time + return_travel
        
        # Check depot closing time
        if return_time > self.depot.ltw:
            return False
        
        return True


def test_clarke_wright():
    """Quick test"""
    import os
    
    print("="*80)
    print("CLARKE-WRIGHT TEST")
    print("="*80)
    
    instance = Instance()
    instance.read_from_file("../instances/pdp_100/lc101.txt")
    
    print(f"Instance: lc101")
    print(f"Nodes: {instance.size}")
    print(f"Capacity: {instance.capacity}")
    
    cw = ClarkeWrightPDPTW(instance)
    routes = cw.solve(max_time=30.0)
    
    # Calculate cost
    total_cost = 0
    for route in routes:
        current = 0
        for node_idx in route:
            total_cost += instance.get_travel_time(current, node_idx)
            current = node_idx
        total_cost += instance.get_travel_time(current, 0)
    
    print(f"\n{'='*80}")
    print(f"RESULT:")
    print(f"  Vehicles: {len(routes)}")
    print(f"  Cost: {total_cost}")
    
    # Validate
    from feasibility_validator import validate_solution
    solution = Solution()
    solution.routes = routes
    is_feasible, violations = validate_solution(solution, instance)
    print(f"  Feasible: {is_feasible}")
    if not is_feasible:
        print(f"  Violations: {len(violations)}")
        for v in violations[:5]:
            print(f"    - {v}")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_clarke_wright()
