"""
Test Multi-Start + SA Vehicles-First on lc101
==============================================
Combines two most impactful improvements
"""

import time
from data_loader import Instance
from multi_start_ils import MultiStartILS
from bks_li_lim import LI_LIM_BKS

print("="*80)
print("TEST: MULTI-START + SA VEHICLES-FIRST")
print("="*80)
print("Improvements:")
print("  - Multi-start: 10 trials x 30s = 300s total")
print("  - SA acceptance (vehicles-first) instead of LAHC")
print("="*80)

instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

start = time.time()
ms = MultiStartILS(
    instance, 
    num_trials=10,      # 10 independent runs
    time_per_trial=30   # 30s each = 300s total (5 min)
)
result = ms.solve()
runtime = time.time() - start

if result:
    bks = LI_LIM_BKS.get('lc101', {})
    bks_veh = bks.get('vehicles', result['vehicles'])
    bks_dist = bks.get('cost', result['cost'])
    
    gap_veh = ((result['vehicles'] - bks_veh) / bks_veh * 100)
    gap_dist = ((result['cost'] - bks_dist) / bks_dist * 100)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULT:")
    print(f"  Vehicles: {result['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh:+.1f}%")
    print(f"  Distance: {result['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist:+.1f}%")
    print(f"  Feasible: {result.get('feasible', True)}")
    print(f"  Runtime: {runtime:.1f}s")
    
    print(f"\n{'='*80}")
    print(f"COMPARISON:")
    print(f"  Phase 1 (single run): 20 veh (+100%), 1421 dist (+71%)")
    print(f"  Multi-start + SA: {result['vehicles']} veh ({gap_veh:+.0f}%), {result['cost']:.0f} dist ({gap_dist:+.0f}%)")
    
    if result['vehicles'] < 20:
        print(f"\n  VEHICLES IMPROVED! ✓✓✓")
    if gap_dist < 71:
        print(f"  DISTANCE IMPROVED! ✓✓")
    
    print(f"{'='*80}")
else:
    print("FAILED")
