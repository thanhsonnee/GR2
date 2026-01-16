"""
FAST TEST for Li & Lim PDPTW Benchmark
Tests a representative SUBSET (10 instances) for quick evaluation
Time: ~3-5 minutes
"""

import os
import time
import json
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from feasibility_validator import validate_solution
from bks_li_lim import get_bks, calculate_gap


# Representative subset: 2 from each class + difficulty mix
TEST_INSTANCES = [
    # LC1 - tight time windows, short horizon
    "../instances/pdp_100/lc101.txt",  # Easy
    "../instances/pdp_100/lc104.txt",  # Hard
    
    # LC2 - tight time windows, long horizon
    "../instances/pdp_100/lc201.txt",  # Easy
    "../instances/pdp_100/lc204.txt",  # Hard
    
    # LR1 - loose time windows, short horizon
    "../instances/pdp_100/lr101.txt",  # Easy
    "../instances/pdp_100/lr104.txt",  # Hard
    
    # LR2 - loose time windows, long horizon
    "../instances/pdp_100/lr201.txt",  # Easy
    "../instances/pdp_100/lr204.txt",  # Hard
    
    # LRC1 - mixed time windows, short horizon
    "../instances/pdp_100/lrc101.txt",  # Easy
    "../instances/pdp_100/lrc104.txt",  # Hard
]

TIME_LIMIT_PER_INSTANCE = 20  # seconds


def test_single_instance(instance_file):
    """Test a single instance"""
    instance_name = os.path.basename(instance_file).replace('.txt', '')
    
    print(f"\nTesting {instance_name}...")
    print("-" * 60)
    
    try:
        # Load instance
        instance = Instance()
        instance.read_from_file(instance_file)
        
        # Run ILS
        start_time = time.time()
        ils = IteratedLocalSearch(
            instance,
            max_iterations=20,
            max_time=TIME_LIMIT_PER_INSTANCE
        )
        
        result = ils.solve()
        runtime = time.time() - start_time
        
        if result is None:
            print(f"  [FAILED] Could not find feasible solution")
            return None
        
        # Extract results
        vehicles = result.get('vehicles', -1)
        cost = result.get('cost', -1)
        is_feasible = result.get('is_feasible', False)
        
        # Get BKS
        bks = get_bks(instance_name)
        if bks:
            gap_veh = calculate_gap(vehicles, bks['vehicles'])
            gap_cost = calculate_gap(cost, bks['cost'])
            
            print(f"  Result: {vehicles} veh, {cost:.0f} cost, {runtime:.1f}s")
            print(f"  BKS:    {bks['vehicles']} veh, {bks['cost']:.2f} cost")
            print(f"  GAP:    {gap_veh:+.1f}% (veh), {gap_cost:+.1f}% (cost)")
            print(f"  Status: {'[OK] FEASIBLE' if is_feasible else '[X] INFEASIBLE'}")
            
            return {
                'instance': instance_name,
                'feasible': is_feasible,
                'vehicles': vehicles,
                'cost': cost,
                'runtime': runtime,
                'bks_vehicles': bks['vehicles'],
                'bks_cost': bks['cost'],
                'gap_vehicles': gap_veh,
                'gap_cost': gap_cost
            }
        else:
            print(f"  Result: {vehicles} veh, {cost:.0f} cost, {runtime:.1f}s")
            print(f"  BKS:    Not available")
            print(f"  Status: {'[OK] FEASIBLE' if is_feasible else '[X] INFEASIBLE'}")
            
            return {
                'instance': instance_name,
                'feasible': is_feasible,
                'vehicles': vehicles,
                'cost': cost,
                'runtime': runtime
            }
    
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run fast test on subset"""
    print("=" * 80)
    print("LI & LIM PDPTW - FAST TEST (SUBSET)")
    print("=" * 80)
    print(f"Testing {len(TEST_INSTANCES)} representative instances")
    print(f"Time limit: {TIME_LIMIT_PER_INSTANCE}s per instance")
    print(f"Estimated total time: {len(TEST_INSTANCES) * TIME_LIMIT_PER_INSTANCE / 60:.1f} minutes")
    print("=" * 80)
    
    results = []
    start_time_total = time.time()
    
    for i, instance_file in enumerate(TEST_INSTANCES, 1):
        print(f"\n[{i}/{len(TEST_INSTANCES)}]")
        result = test_single_instance(instance_file)
        if result:
            results.append(result)
    
    total_time = time.time() - start_time_total
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - FAST TEST")
    print("=" * 80)
    
    feasible_count = sum(1 for r in results if r['feasible'])
    print(f"\nTotal tested: {len(results)}/{len(TEST_INSTANCES)}")
    print(f"Feasible: {feasible_count}/{len(results)} ({100*feasible_count/max(len(results),1):.1f}%)")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    if results:
        avg_gap_veh = sum(r.get('gap_vehicles', 0) for r in results) / len(results)
        avg_gap_cost = sum(r.get('gap_cost', 0) for r in results) / len(results)
        
        print(f"\nAverage gaps:")
        print(f"  Vehicles: {avg_gap_veh:+.1f}%")
        print(f"  Cost:     {avg_gap_cost:+.1f}%")
        
        # Best and worst
        best_result = min(results, key=lambda x: x.get('gap_cost', 999))
        worst_result = max(results, key=lambda x: x.get('gap_cost', 0))
        
        print(f"\nBest gap:  {best_result['instance']} ({best_result.get('gap_cost', 0):+.1f}%)")
        print(f"Worst gap: {worst_result['instance']} ({worst_result.get('gap_cost', 0):+.1f}%)")
    
    # Save results
    with open('fast_test_results.json', 'w') as f:
        json.dump({
            'benchmark': 'Li & Lim PDPTW - Fast Test',
            'instances': len(TEST_INSTANCES),
            'time_limit': TIME_LIMIT_PER_INSTANCE,
            'total_time': total_time,
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to: fast_test_results.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
