"""
FULL TEST - Phase 1 Improvements on 29 instances
"""
import os
import sys
import time
import json
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from bks_li_lim import LI_LIM_BKS

sys.stdout.reconfigure(encoding='utf-8')

target_instances = [
    'lc101', 'lc102', 'lc103', 'lc104', 'lc105', 'lc106', 'lc107', 'lc108', 'lc109',
    'lr101', 'lr102', 'lr103', 'lr104', 'lr105', 'lr106', 
    'lr107', 'lr108', 'lr109', 'lr110', 'lr111', 'lr112',
    'lrc101', 'lrc102', 'lrc103', 'lrc104', 'lrc105', 'lrc106', 'lrc107', 'lrc108'
]

instances_dir = "../instances/pdp_100"
results = []

print("="*80)
print("PHASE 1 FULL TEST - 29 Instances")
print("="*80)
print("Improvements:")
print("  1. Lexicographic (vehicles, cost)")
print("  2. Route Elimination after AGES")
print("  3. Worst Removal operator")
print("  4. Variable Regret-k (k=2..5)")
print("="*80)
print(f"Time limit: 180s/instance")
print(f"Expected total: ~90 minutes")
print("="*80)

start_all = time.time()

for idx, inst_name in enumerate(target_instances, 1):
    print(f"\n[{idx}/{len(target_instances)}] Testing {inst_name}...")
    
    instance_file = os.path.join(instances_dir, f"{inst_name}.txt")
    
    if not os.path.exists(instance_file):
        print(f"  [SKIP] File not found")
        continue
    
    try:
        instance = Instance()
        instance.read_from_file(instance_file)
        
        start_time = time.time()
        ils = IteratedLocalSearch(
            instance,
            max_iterations=20,
            max_time=180,
            no_improvement_limit=999
        )
        result = ils.solve()
        runtime = time.time() - start_time
        
        if result is None:
            print(f"  [FAILED] No solution")
            continue
        
        bks = LI_LIM_BKS.get(inst_name, {})
        bks_veh = bks.get('vehicles', result['vehicles'])
        bks_dist = bks.get('cost', result['cost'])
        
        gap_veh = ((result['vehicles'] - bks_veh) / bks_veh * 100)
        gap_dist = ((result['cost'] - bks_dist) / bks_dist * 100)
        
        result_data = {
            'instance': inst_name,
            'vehicles': result['vehicles'],
            'distance': result['cost'],
            'feasible': result.get('feasible', True),
            'runtime': runtime,
            'bks_vehicles': bks_veh,
            'bks_distance': bks_dist,
            'gap_vehicles': gap_veh,
            'gap_distance': gap_dist
        }
        results.append(result_data)
        
        print(f"  Result: {result['vehicles']} veh, {result['cost']:.0f} dist")
        print(f"  BKS: {bks_veh} veh, {bks_dist:.2f} dist")
        print(f"  Gap: {gap_dist:+.1f}%")
        
        if gap_dist <= 5:
            print(f"  >>> EXCELLENT! <<<")
        elif gap_dist <= 10:
            print(f"  >> VERY GOOD <<")
        elif gap_dist <= 25:
            print(f"  > ON TARGET <")
        
        # Save progress
        with open('phase1_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

# Final report
if results:
    avg_gap = sum(r['gap_distance'] for r in results) / len(results)
    excellent = sum(1 for r in results if r['gap_distance'] <= 5)
    very_good = sum(1 for r in results if r['gap_distance'] <= 10)
    good = sum(1 for r in results if r['gap_distance'] <= 20)
    acceptable = sum(1 for r in results if r['gap_distance'] <= 30)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS:")
    print(f"  Completed: {len(results)}/{len(target_instances)}")
    print(f"  Average gap: {avg_gap:.1f}%")
    print(f"  Gap <=5%: {excellent} instances")
    print(f"  Gap <=10%: {very_good} instances")
    print(f"  Gap <=20%: {good} instances")
    print(f"  Gap <=30%: {acceptable} instances")
    print(f"  Total time: {(time.time()-start_all)/60:.1f} min")
    
    if avg_gap <= 25:
        print(f"\n  TARGET ACHIEVED! Gap {avg_gap:.1f}% <= 25%")
    elif avg_gap <= 40:
        print(f"\n  GOOD PROGRESS! Gap {avg_gap:.1f}%")
    else:
        print(f"\n  More improvements needed. Gap {avg_gap:.1f}%")
    
    print(f"{'='*80}")
