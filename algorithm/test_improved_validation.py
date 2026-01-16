#!/usr/bin/env python3
"""
Improved validation test suite with strict feasibility checking
"""

import time
from data_loader import Instance, Solution
from construction_heuristic import GreedyInsertion
from large_neighborhood_search import LargeNeighborhoodSearch
from local_search import LocalSearch
from solution_encoder import SolutionEncoder

def test_with_improved_validation(instance_file: str):
    """Test with strict validation and sanity checks"""
    print("="*70)
    print(f"IMPROVED VALIDATION TEST: {instance_file}")
    print("="*70)
    
    # Load instance
    instance = Instance()
    instance.read_from_file(instance_file)
    
    print(f"Instance: {instance.name}")
    print(f"Customers: {instance.size-1}")
    print(f"Pickup-delivery pairs: {len(instance.get_pickup_delivery_pairs())}")
    print(f"Capacity: {instance.capacity}")
    
    # Calculate expected bounds
    num_pairs = len(instance.get_pickup_delivery_pairs())
    min_vehicles_expected = max(3, num_pairs // 12)
    max_vehicles_expected = min(num_pairs // 2, 15)  # Upper bound
    
    print(f"Expected vehicles: {min_vehicles_expected} - {max_vehicles_expected}")
    print("-"*70)
    
    # Test 1: Construction Heuristic
    print("\n1. CONSTRUCTION HEURISTIC TEST")
    print("-"*40)
    
    constructor = GreedyInsertion(instance)
    start_time = time.time()
    routes = constructor.solve()
    construction_time = time.time() - start_time
    
    if not routes:
        print("❌ Construction failed to create any routes")
        return
    
    construction_solution = SolutionEncoder.create_solution_from_routes(
        routes, instance.name, "Construction"
    )
    
    # Validate construction
    validator = LocalSearch(instance)
    is_construction_valid = validator._is_valid_solution(construction_solution)
    
    vehicles = construction_solution.get_num_vehicles()
    cost = construction_solution.get_cost(instance)
    
    print(f"Vehicles: {vehicles}")
    print(f"Cost: {cost}")
    print(f"Valid: {'YES' if is_construction_valid else 'NO'}")
    print(f"Time: {construction_time:.2f}s")
    
    # Sanity check
    if vehicles < min_vehicles_expected:
        print(f"[WARNING] Too few vehicles ({vehicles} < {min_vehicles_expected})")
    elif vehicles > max_vehicles_expected:
        print(f"[WARNING] Too many vehicles ({vehicles} > {max_vehicles_expected})")
    else:
        print(f"[OK] Vehicle count within expected range")
    
    # Test 2: LNS with Strict Validation
    print(f"\n2. LNS WITH STRICT VALIDATION TEST")
    print("-"*40)
    
    if is_construction_valid:
        print("Starting with feasible construction solution...")
        lns = LargeNeighborhoodSearch(
            instance, 
            max_iterations=100, 
            max_time=30
        )
        lns.current_solution = construction_solution
        lns.best_solution = lns._copy_solution(construction_solution)
        
        start_time = time.time()
        lns_solution = lns.solve()
        lns_time = time.time() - start_time
        
        if lns_solution:
            lns_vehicles = lns_solution.get_num_vehicles()
            lns_cost = lns_solution.get_cost(instance)
            is_lns_valid = validator._is_valid_solution(lns_solution)
            
            print(f"LNS Vehicles: {lns_vehicles}")
            print(f"LNS Cost: {lns_cost}")
            print(f"LNS Valid: {'YES' if is_lns_valid else 'NO'}")
            print(f"LNS Time: {lns_time:.2f}s")
            
            # Improvement analysis
            if lns_vehicles <= vehicles and lns_cost <= cost:
                vehicle_improvement = vehicles - lns_vehicles
                cost_improvement = cost - lns_cost
                print(f"[IMPROVEMENT] -{vehicle_improvement} vehicles, -{cost_improvement} cost")
            else:
                print(f"[WARNING] No improvement or degradation")
        else:
            print("[ERROR] LNS failed to produce solution")
    else:
        print("[ERROR] Skipping LNS test - construction not feasible")
    
    # Test 3: Compare with Best Known
    print(f"\n3. BEST KNOWN COMPARISON")
    print("-"*40)
    
    try:
        with open('../solutions/bks.dat', 'r') as f:
            for line in f:
                if line.startswith(instance.name):
                    parts = line.strip().split(';')
                    if len(parts) >= 4:
                        bk_vehicles = int(parts[2])
                        bk_cost = int(parts[3])
                        
                        print(f"Best Known: {bk_vehicles} vehicles, {bk_cost} cost")
                        
                        if is_construction_valid:
                            vehicle_gap = ((vehicles - bk_vehicles) / bk_vehicles) * 100
                            cost_gap = ((cost - bk_cost) / bk_cost) * 100
                            
                            print(f"Construction Gap: {vehicle_gap:.2f}% vehicles, {cost_gap:.2f}% cost")
                            
                            if 'lns_solution' in locals() and lns_solution and is_lns_valid:
                                lns_vehicle_gap = ((lns_vehicles - bk_vehicles) / bk_vehicles) * 100
                                lns_cost_gap = ((lns_cost - bk_cost) / bk_cost) * 100
                                print(f"LNS Gap: {lns_vehicle_gap:.2f}% vehicles, {lns_cost_gap:.2f}% cost")
                        
                        break
    except FileNotFoundError:
        print("Best known solutions file not found")
    
    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)

def run_multiple_tests():
    """Run tests on multiple instances"""
    test_instances = [
        "../instances/bar-n100-1.txt",
        "../instances/n100/n100/bar-n100-2.txt", 
        "../instances/n100/n100/ber-n100-1.txt",
        "../instances/n100/n100/nyc-n100-1.txt"
    ]
    
    results = []
    
    for instance_file in test_instances:
        try:
            print(f"\n{'='*20} TESTING {instance_file} {'='*20}")
            test_with_improved_validation(instance_file)
            results.append(f"[OK] {instance_file}: COMPLETED")
        except Exception as e:
            print(f"[ERROR] testing {instance_file}: {e}")
            results.append(f"[ERROR] {instance_file}: FAILED - {e}")
    
    print(f"\n{'='*70}")
    print("SUMMARY RESULTS")
    print("="*70)
    for result in results:
        print(result)

if __name__ == "__main__":
    print("IMPROVED VALIDATION TEST SUITE")
    print("Testing with strict feasibility checking and sanity bounds")
    run_multiple_tests()
