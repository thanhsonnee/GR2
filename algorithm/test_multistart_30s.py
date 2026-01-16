"""
Multi-Start ILS with 30s per trial
===================================
Enough time for full optimization pipeline
"""

import time
from data_loader import Instance
from multi_start_ils import MultiStartILS
from bks_li_lim import LI_LIM_BKS

print("="*80)
print("MULTI-START ILS - 30s per trial")
print("="*80)
print("Config: 10 trials × 30s = 300s (5 minutes)")
print("Each trial runs full pipeline:")
print("  - Clarke-Wright initial")
print("  - AGES + Route Elimination")
print("  - LNS optimization")
print("  - Route Improvement")
print("="*80)

instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

start = time.time()
ms = MultiStartILS(
    instance, 
    num_trials=10,      # 10 independent runs
    time_per_trial=30   # 30s each = enough for full optimization
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
    print(f"FINAL BEST RESULT:")
    print(f"  Vehicles: {result['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh:+.1f}%")
    print(f"  Distance: {result['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist:+.1f}%")
    print(f"  Feasible: {result.get('feasible', True)}")
    print(f"  Total Runtime: {runtime:.1f}s")
    
    print(f"\n{'='*80}")
    print(f"COMPARISON:")
    print(f"  Phase 1 (120s single): 20 veh (+100%), 1421 dist (+71%)")
    print(f"  Multi-start 15s: 18 veh (+80%), 1696 dist (+105%)")
    print(f"  Multi-start 30s: {result['vehicles']} veh ({gap_veh:+.0f}%), {result['cost']:.0f} dist ({gap_dist:+.0f}%)")
    
    # Check improvements
    improvements = []
    if result['vehicles'] <= 18:
        improvements.append("VEHICLES ≤ 18! ✓✓✓")
    if gap_dist < 71:
        improvements.append("DISTANCE < Phase1! ✓✓")
    if result['vehicles'] <= 18 and gap_dist < 71:
        improvements.append("BOTH IMPROVED! ✓✓✓✓✓")
    
    if improvements:
        print(f"\n  {' | '.join(improvements)}")
    
    print(f"{'='*80}")
else:
    print("FAILED")
