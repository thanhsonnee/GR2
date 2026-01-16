"""
So sánh 3 phương pháp: Phase 1, Multi-start 15s, Multi-start 30s
===================================================================
Chạy file này để ra kết quả như trong bảng so sánh
"""

import time
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from multi_start_ils import MultiStartILS
from bks_li_lim import LI_LIM_BKS

print("="*80)
print("SO SÁNH 3 PHƯƠNG PHÁP - lc101")
print("="*80)

instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

bks = LI_LIM_BKS.get('lc101', {})
bks_veh = bks.get('vehicles', 10)
bks_dist = bks.get('cost', 828.94)

results = {}

# ============================================================================
# METHOD 1: Phase 1 Single (120s)
# ============================================================================
print("\n" + "="*80)
print("METHOD 1: Phase 1 Single (120s)")
print("="*80)

start = time.time()
ils1 = IteratedLocalSearch(
    instance,
    max_iterations=20,
    max_time=120,
    no_improvement_limit=999
)
result1 = ils1.solve()
runtime1 = time.time() - start

if result1:
    gap_veh1 = ((result1['vehicles'] - bks_veh) / bks_veh * 100)
    gap_dist1 = ((result1['cost'] - bks_dist) / bks_dist * 100)
    
    results['phase1'] = {
        'time': runtime1,
        'vehicles': result1['vehicles'],
        'distance': result1['cost'],
        'veh_gap': gap_veh1,
        'dist_gap': gap_dist1
    }
    
    print(f"✓ Vehicles: {result1['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh1:+.1f}%")
    print(f"✓ Distance: {result1['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist1:+.1f}%")
    print(f"✓ Runtime: {runtime1:.1f}s")
else:
    print("✗ FAILED")

# ============================================================================
# METHOD 2: Multi-start 15s (5 trials × 15s = 75s)
# ============================================================================
print("\n" + "="*80)
print("METHOD 2: Multi-start 15s (5 trials × 15s = 75s)")
print("="*80)

start = time.time()
ms2 = MultiStartILS(
    instance,
    num_trials=5,
    time_per_trial=15
)
result2 = ms2.solve()
runtime2 = time.time() - start

if result2:
    gap_veh2 = ((result2['vehicles'] - bks_veh) / bks_veh * 100)
    gap_dist2 = ((result2['cost'] - bks_dist) / bks_dist * 100)
    
    results['multistart_15s'] = {
        'time': runtime2,
        'vehicles': result2['vehicles'],
        'distance': result2['cost'],
        'veh_gap': gap_veh2,
        'dist_gap': gap_dist2
    }
    
    print(f"✓ Vehicles: {result2['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh2:+.1f}%")
    print(f"✓ Distance: {result2['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist2:+.1f}%")
    print(f"✓ Runtime: {runtime2:.1f}s")
else:
    print("✗ FAILED")

# ============================================================================
# METHOD 3: Multi-start 30s (10 trials × 30s = 300s)
# ============================================================================
print("\n" + "="*80)
print("METHOD 3: Multi-start 30s (10 trials × 30s = 300s)")
print("="*80)

start = time.time()
ms3 = MultiStartILS(
    instance,
    num_trials=10,
    time_per_trial=30
)
result3 = ms3.solve()
runtime3 = time.time() - start

if result3:
    gap_veh3 = ((result3['vehicles'] - bks_veh) / bks_veh * 100)
    gap_dist3 = ((result3['cost'] - bks_dist) / bks_dist * 100)
    
    results['multistart_30s'] = {
        'time': runtime3,
        'vehicles': result3['vehicles'],
        'distance': result3['cost'],
        'veh_gap': gap_veh3,
        'dist_gap': gap_dist3
    }
    
    print(f"✓ Vehicles: {result3['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh3:+.1f}%")
    print(f"✓ Distance: {result3['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist3:+.1f}%")
    print(f"✓ Runtime: {runtime3:.1f}s")
else:
    print("✗ FAILED")

# ============================================================================
# SUMMARY TABLE
# ============================================================================
print("\n" + "="*80)
print("BẢNG SO SÁNH KẾT QUẢ")
print("="*80)
print(f"{'Method':<25} {'Time':<10} {'Vehicles':<12} {'Distance':<12} {'Veh Gap':<12} {'Dist Gap':<12}")
print("-"*80)

if 'phase1' in results:
    r = results['phase1']
    print(f"{'Phase 1 single':<25} {r['time']:<10.0f}s {r['vehicles']:<12} {r['distance']:<12.0f} {r['veh_gap']:+.1f}%{'':<7} {r['dist_gap']:+.1f}%")

if 'multistart_15s' in results:
    r = results['multistart_15s']
    print(f"{'Multi-start 15s':<25} {r['time']:<10.0f}s {r['vehicles']:<12} {r['distance']:<12.0f} {r['veh_gap']:+.1f}%{'':<7} {r['dist_gap']:+.1f}%")

if 'multistart_30s' in results:
    r = results['multistart_30s']
    print(f"{'Multi-start 30s':<25} {r['time']:<10.0f}s {r['vehicles']:<12} {r['distance']:<12.0f} {r['veh_gap']:+.1f}%{'':<7} {r['dist_gap']:+.1f}%")

print("="*80)
print(f"\nBKS: {bks_veh} vehicles, {bks_dist:.2f} distance")
print("="*80)
