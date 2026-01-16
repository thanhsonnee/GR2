"""
Test Phase 1 Improvements on lc101
====================================
1. Lexicographic ordering (vehicles, cost) - VERIFIED ✓
2. Route Elimination after AGES
3. Worst Removal operator
4. Variable Regret-k (k=2..5)
"""
import time
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from bks_li_lim import LI_LIM_BKS

print("="*80)
print("PHASE 1 IMPROVEMENTS TEST - lc101")
print("="*80)
print("Improvements:")
print("  1. Lexicographic (vehicles, cost) ordering")
print("  2. Route Elimination after AGES")
print("  3. Worst Removal operator")
print("  4. Variable Regret-k (k=2..5)")
print("="*80)

instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

start = time.time()
ils = IteratedLocalSearch(
    instance,
    max_iterations=20,
    max_time=120,
    no_improvement_limit=999
)
result = ils.solve()
runtime = time.time() - start

if result:
    bks = LI_LIM_BKS.get('lc101', {})
    bks_veh = bks.get('vehicles', result['vehicles'])
    bks_dist = bks.get('cost', result['cost'])
    
    gap_veh = ((result['vehicles'] - bks_veh) / bks_veh * 100)
    gap_dist = ((result['cost'] - bks_dist) / bks_dist * 100)
    
    print(f"\n{'='*80}")
    print(f"RESULT:")
    print(f"  Vehicles: {result['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh:+.1f}%")
    print(f"  Distance: {result['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist:+.1f}%")
    print(f"  Feasible: {result.get('feasible', True)}")
    print(f"  Runtime: {runtime:.1f}s")
    print(f"\n{'='*80}")
    print(f"COMPARISON:")
    print(f"  Old (Greedy): 18 veh (+80%), 2315 dist (+179%)")
    print(f"  Old (CW): 24 veh (+140%), 1895 dist (+129%)")
    print(f"  New (Phase1): {result['vehicles']} veh ({gap_veh:+.0f}%), {result['cost']:.0f} dist ({gap_dist:+.0f}%)")
    
    if result['vehicles'] < 18:
        print(f"\n  VEHICLES IMPROVED! ✓✓✓")
    elif gap_dist < 100:
        print(f"\n  DISTANCE IMPROVED SIGNIFICANTLY! ✓✓")
    else:
        print(f"\n  Still needs improvement")
    print(f"{'='*80}")
else:
    print("FAILED")
