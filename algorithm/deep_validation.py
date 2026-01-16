#!/usr/bin/env python3
"""
Deep validation tool to verify solution feasibility
"""

from data_loader import Instance, Solution
from local_search import LocalSearch
import sys

def validate_solution_thoroughly(instance_file: str, solution_or_routes):
    """Thoroughly validate a solution"""
    
    print("="*60)
    print("DEEP SOLUTION VALIDATION")
    print("="*60)
    
    # Load instance
    instance = Instance()
    instance.read_from_file(instance_file)
    
    print(f"Instance: {instance.name}")
    print(f"Customers: {instance.size-1}")
    print(f"Capacity: {instance.capacity}")
    print(f"Pickup-delivery pairs: {len(instance.get_pickup_delivery_pairs())}")
    
    # Handle solution input
    if isinstance(solution_or_routes, list):
        # Routes provided
        routes = solution_or_routes
        solution = Solution()
        solution.routes = routes
        solution.inst_name = instance.name
    else:
        # Solution object provided
        solution = solution_or_routes
        routes = solution.routes
    
    print(f"\nSolution routes: {len(routes)}")
    for i, route in enumerate(routes):
        print(f"Route {i+1}: {route} ({len(route)} nodes)")
    
    # Calculate cost
    total_cost = solution.get_cost(instance)
    print(f"\nTotal cost: {total_cost}")
    
    # Deep validation
    validator = LocalSearch(instance)
    
    print(f"\n{'='*60}")
    print("CONSTRAINT CHECKING")
    print("="*60)
    
    # 1. Check each route individually
    all_routes_valid = True
    for i, route in enumerate(routes):
        print(f"\n--- Route {i+1} Analysis ---")
        is_valid = validator._is_feasible_route(route)
        print(f"Route valid: {is_valid}")
        
        if not is_valid:
            all_routes_valid = False
            # Detailed constraint checking
            check_route_constraints(route, instance)
    
    # 2. Check global constraints
    print(f"\n--- Global Constraints ---")
    
    # All customers served exactly once
    all_customers = set()
    for route in routes:
        for node in route:
            if node != 0:  # Exclude depot
                if node in all_customers:
                    print(f"❌ Customer {node} served multiple times")
                    all_routes_valid = False
                all_customers.add(node)
    
    required_customers = set(range(1, instance.size))
    missing_customers = required_customers - all_customers
    extra_customers = all_customers - required_customers
    
    if missing_customers:
        print(f"❌ Missing customers: {missing_customers}")
        all_routes_valid = False
    
    if extra_customers:
        print(f"❌ Extra/invalid customers: {extra_customers}")
        all_routes_valid = False
    
    if not missing_customers and not extra_customers:
        print(f"✅ All {len(required_customers)} customers served exactly once")
    
    # 3. Overall validation
    overall_valid = validator._is_valid_solution(solution)
    print(f"\nOverall solution valid: {overall_valid}")
    
    # 4. Compare with best known
    try:
        with open('../solutions/bks.dat', 'r') as f:
            for line in f:
                if line.startswith(instance.name):
                    parts = line.strip().split(';')
                    if len(parts) >= 4:
                        bk_vehicles = int(parts[2])
                        bk_cost = int(parts[3])
                        
                        print(f"\n--- Benchmark Comparison ---")
                        print(f"Our result:     {len(routes)} vehicles, cost {total_cost}")
                        print(f"Best known:     {bk_vehicles} vehicles, cost {bk_cost}")
                        
                        vehicle_gap = ((len(routes) - bk_vehicles) / bk_vehicles) * 100
                        cost_gap = ((total_cost - bk_cost) / bk_cost) * 100
                        
                        print(f"Vehicle gap:    {vehicle_gap:.2f}%")
                        print(f"Cost gap:       {cost_gap:.2f}%")
                        
                        if vehicle_gap < -10 or cost_gap < -10:
                            print("🚨 WARNING: Result significantly better than best known - likely infeasible!")
                        
                        break
    except:
        print("Could not load best known solutions")
    
    return all_routes_valid and overall_valid

def check_route_constraints(route, instance):
    """Check detailed constraints for a single route"""
    if not route:
        return True
    
    time = 0
    load = 0
    visited_pickups = set()
    prev_node = 0
    
    print(f"Route constraint check: {route}")
    
    for i, node_id in enumerate(route):
        node = instance.nodes[node_id]
        
        # Travel time
        travel_time = instance.get_travel_time(prev_node, node_id)
        time += travel_time
        arrival_time = max(time, node.etw)
        
        # Check time window
        if arrival_time > node.ltw:
            print(f"  ❌ Node {node_id} at pos {i}: Time window violation ({arrival_time} > {node.ltw})")
        
        # Check capacity
        load += node.dem
        if load > instance.capacity:
            print(f"  ❌ Node {node_id} at pos {i}: Capacity violation ({load} > {instance.capacity})")
        if load < 0:
            print(f"  ❌ Node {node_id} at pos {i}: Negative load ({load})")
        
        # Check precedence
        if node.is_delivery():
            pickup_node_id = node.pair
            if pickup_node_id not in visited_pickups:
                print(f"  ❌ Node {node_id} at pos {i}: Delivery before pickup (pickup {pickup_node_id} not visited)")
        
        if node.is_pickup():
            visited_pickups.add(node_id)
        
        time = arrival_time + node.dur
        prev_node = node_id
        
        print(f"  Node {node_id}: time={arrival_time}, load={load}, demand={node.dem}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deep_validation.py <instance_file>")
        sys.exit(1)
    
    # Test with latest ILS result
    from iterated_local_search import IteratedLocalSearch
    from construction_heuristic import GreedyInsertion
    from solution_encoder import SolutionEncoder
    
    instance_file = sys.argv[1]
    instance = Instance()
    instance.read_from_file(instance_file)
    
    # Run ILS
    print("Running ILS to get solution...")
    ils = IteratedLocalSearch(instance, max_iterations=1, max_time=30)
    results = ils.solve()
    
    if results and results.get('solution'):
        validate_solution_thoroughly(instance_file, results['solution'])
    else:
        print("No solution found from ILS")
