"""
AGGRESSIVE TEST - Target: gap ≤5% for some instances
Focus on: lc101-109, lr101-112, lrc101-108 (29 instances)

Improvements:
- Time limit: 120s per instance
- No early stopping
- LNS iterations: 2000
- Destroy size: 10-50
- ILS iterations: 20
"""

import os
import sys
import time
import json
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from bks_li_lim import LI_LIM_BKS

def test_aggressive():
    """Aggressive test for better results"""
    
    # Target instances (29 total)
    target_instances = [
        # LC1 (9 instances)
        'lc101', 'lc102', 'lc103', 'lc104', 'lc105', 'lc106', 'lc107', 'lc108', 'lc109',
        # LR1 (12 instances)
        'lr101', 'lr102', 'lr103', 'lr104', 'lr105', 'lr106', 
        'lr107', 'lr108', 'lr109', 'lr110', 'lr111', 'lr112',
        # LRC1 (8 instances)
        'lrc101', 'lrc102', 'lrc103', 'lrc104', 'lrc105', 'lrc106', 'lrc107', 'lrc108'
    ]
    
    instances_dir = "../instances/pdp_100"
    results = []
    
    print("=" * 80)
    print("AGGRESSIVE TEST - Target: gap <=5%")
    print("=" * 80)
    print(f"Instances: {len(target_instances)}")
    print(f"Time limit: 120s per instance")
    print(f"Config: LNS 2000 iter, Destroy 10-50, ILS 20 iter, No early stopping")
    print("=" * 80)
    
    start_all = time.time()
    
    for idx, inst_name in enumerate(target_instances, 1):
        print(f"\n[{idx}/{len(target_instances)}] Testing {inst_name}...")
        
        instance_file = os.path.join(instances_dir, f"{inst_name}.txt")
        
        if not os.path.exists(instance_file):
            print(f"  [SKIP] File not found: {instance_file}")
            continue
        
        try:
            # Load instance
            instance = Instance()
            instance.read_from_file(instance_file)
            
            # Run ILS with AGGRESSIVE parameters
            start_time = time.time()
            ils = IteratedLocalSearch(
                instance,
                max_iterations=20,  # More iterations
                max_time=120,  # 2 minutes per instance
                no_improvement_limit=999  # Effectively disable early stopping
            )
            result = ils.solve()
            runtime = time.time() - start_time
            
            if result is None:
                print(f"  [FAILED] No feasible solution found")
                continue
            
            # Get BKS
            bks = LI_LIM_BKS.get(inst_name, {})
            bks_veh = bks.get('vehicles', result['vehicles'])
            bks_dist = bks.get('cost', result['cost'])
            
            # Calculate gaps
            gap_veh = ((result['vehicles'] - bks_veh) / bks_veh * 100) if bks_veh > 0 else 0
            gap_dist = ((result['cost'] - bks_dist) / bks_dist * 100) if bks_dist > 0 else 0
            
            result_entry = {
                'instance': inst_name,
                'vehicles': result['vehicles'],
                'cost': result['cost'],
                'distance': result['cost'],
                'feasible': result.get('is_feasible', True),
                'runtime': runtime,
                'bks_vehicles': bks_veh,
                'bks_distance': bks_dist,
                'gap_vehicles': gap_veh,
                'gap_distance': gap_dist
            }
            results.append(result_entry)
            
            # Print result
            status = "[OK]" if result.get('is_feasible', True) else "[X]"
            print(f"  {status} Result: {result['vehicles']} veh, {result['cost']:.0f} dist, "
                  f"time={runtime:.1f}s")
            print(f"      BKS: {bks_veh} veh, {bks_dist:.2f} dist")
            print(f"      Gap: {gap_veh:+.1f}% veh, {gap_dist:+.1f}% dist", end="")
            
            # Highlight good results
            if gap_dist <= 5:
                print(" *** EXCELLENT! ***")
            elif gap_dist <= 10:
                print(" ** VERY GOOD **")
            elif gap_dist <= 20:
                print(" * GOOD *")
            else:
                print()
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            continue
    
    total_time = time.time() - start_all
    
    # Save results
    with open('aggressive_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("AGGRESSIVE TEST SUMMARY")
    print("=" * 80)
    
    if results:
        feasible_count = sum(1 for r in results if r.get('feasible', True))
        print(f"Total: {len(results)}/{len(target_instances)}")
        print(f"Feasible: {feasible_count}/{len(results)} ({100*feasible_count/len(results):.1f}%)")
        print(f"Total time: {total_time/60:.1f} min")
        print(f"Avg time: {total_time/len(results):.1f}s per instance")
        
        # Gap analysis
        gaps_dist = [r['gap_distance'] for r in results if r.get('feasible', True)]
        if gaps_dist:
            avg_gap = sum(gaps_dist) / len(gaps_dist)
            min_gap = min(gaps_dist)
            max_gap = max(gaps_dist)
            
            print(f"\nGap statistics:")
            print(f"  Average: {avg_gap:.1f}%")
            print(f"  Best: {min_gap:.1f}%")
            print(f"  Worst: {max_gap:.1f}%")
            
            # Count by range
            excellent = sum(1 for g in gaps_dist if g <= 5)
            very_good = sum(1 for g in gaps_dist if 5 < g <= 10)
            good = sum(1 for g in gaps_dist if 10 < g <= 20)
            acceptable = sum(1 for g in gaps_dist if 20 < g <= 50)
            poor = sum(1 for g in gaps_dist if g > 50)
            
            print(f"\nGap distribution:")
            print(f"  <=5%  (EXCELLENT): {excellent}/{len(gaps_dist)} ({100*excellent/len(gaps_dist):.1f}%)")
            print(f"  5-10% (VERY GOOD): {very_good}/{len(gaps_dist)} ({100*very_good/len(gaps_dist):.1f}%)")
            print(f"  10-20% (GOOD): {good}/{len(gaps_dist)} ({100*good/len(gaps_dist):.1f}%)")
            print(f"  20-50% (ACCEPTABLE): {acceptable}/{len(gaps_dist)} ({100*acceptable/len(gaps_dist):.1f}%)")
            print(f"  >50% (POOR): {poor}/{len(gaps_dist)} ({100*poor/len(gaps_dist):.1f}%)")
            
            # List excellent results
            if excellent > 0:
                print(f"\n{'='*80}")
                print("EXCELLENT RESULTS (gap <=5%):")
                print(f"{'='*80}")
                for r in results:
                    if r.get('feasible', True) and r['gap_distance'] <= 5:
                        print(f"  {r['instance']}: {r['vehicles']} veh ({r['bks_vehicles']} BKS), "
                              f"{r['distance']:.2f} dist ({r['bks_distance']:.2f} BKS), "
                              f"gap={r['gap_distance']:+.2f}%")
    
    print("=" * 80)

if __name__ == "__main__":
    test_aggressive()
