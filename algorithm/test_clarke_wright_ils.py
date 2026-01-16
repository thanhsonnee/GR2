"""
Quick test: Clarke-Wright + ILS on lc101
"""
import time
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from bks_li_lim import LI_LIM_BKS

instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

print("="*80)
print("TEST: CLARKE-WRIGHT + ILS on lc101")
print("="*80)

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
    print(f"  Cost: {result['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist:+.1f}%")
    print(f"  Feasible: {result.get('feasible', True)}")
    print(f"  Runtime: {runtime:.1f}s")
    print(f"{'='*80}")
else:
    print("FAILED")
