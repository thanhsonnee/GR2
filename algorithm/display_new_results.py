"""
Display NEW results with clean format and BKS comparison
"""
import json
import os
from bks_li_lim import get_bks, calculate_gap

results_file = "li_lim_results.json"

if not os.path.exists(results_file):
    print("ERROR: Results file not found!")
    exit(1)

with open(results_file, 'r') as f:
    data = json.load(f)

results = data.get('results', [])

print("=" * 130)
print("LI & LIM PDPTW - NEW RESULTS (30s, Destroy 8-30, LNS 500 iter)")
print("=" * 130)
print(f"Total: {len(results)} instances | Time limit: {data.get('time_limit', 30)}s")
print("=" * 130)
print()

# Display results
for i, r in enumerate(results, 1):
    inst = r['instance']
    veh = r['vehicles']
    cost = r['cost']
    dist = cost
    feas = "True " if r.get('feasible', False) else "False"
    time = r.get('runtime', 0)
    
    bks = get_bks(inst)
    
    print(f"[{i:2d}/56] Testing {inst:8s}... Result: {veh:2d} veh, cost {cost:7.2f}, distance {dist:7.2f}, feasible={feas:5s}, time={time:4.1f}s", end="")
    
    if bks:
        gap_v = calculate_gap(veh, bks['vehicles'])
        gap_d = calculate_gap(dist, bks['cost'])
        print(f"  | BKS: {bks['vehicles']:2d} veh, {bks['cost']:7.2f} dist | Gap: {gap_v:+5.1f}% veh, {gap_d:+5.1f}% dist")
    else:
        print()

# Summary
print()
print("=" * 130)
print("SUMMARY")
print("=" * 130)

feasible = sum(1 for r in results if r.get('feasible', False))
total_time = data.get('total_time', sum(r.get('runtime', 0) for r in results))

print(f"\nTotal:     {len(results)}")
print(f"Feasible:  {feasible}/{len(results)} ({100*feasible/len(results):.1f}%)")
print(f"Time:      {total_time/60:.1f} min ({total_time:.0f}s)")
print(f"Avg/inst:  {total_time/len(results):.1f}s")

# Calculate gaps with BKS
gaps_v = []
gaps_d = []
for r in results:
    bks = get_bks(r['instance'])
    if bks:
        gaps_v.append(calculate_gap(r['vehicles'], bks['vehicles']))
        gaps_d.append(calculate_gap(r['cost'], bks['cost']))

if gaps_v:
    avg_gap_v = sum(gaps_v) / len(gaps_v)
    avg_gap_d = sum(gaps_d) / len(gaps_d)
    
    print(f"\nAverage gaps:")
    print(f"  Vehicles:  {avg_gap_v:+.1f}%")
    print(f"  Distance:  {avg_gap_d:+.1f}%")
    
    best_idx = gaps_d.index(min(gaps_d))
    worst_idx = gaps_d.index(max(gaps_d))
    
    print(f"\nBest:  {results[best_idx]['instance']} (gap: {gaps_d[best_idx]:+.1f}%)")
    print(f"Worst: {results[worst_idx]['instance']} (gap: {gaps_d[worst_idx]:+.1f}%)")
    
    # Distribution
    ranges = {
        '<20%': sum(1 for g in gaps_d if g < 20),
        '20-30%': sum(1 for g in gaps_d if 20 <= g < 30),
        '30-50%': sum(1 for g in gaps_d if 30 <= g < 50),
        '>50%': sum(1 for g in gaps_d if g >= 50)
    }
    
    print(f"\nGap distribution:")
    for name, count in ranges.items():
        pct = 100 * count / len(gaps_d)
        print(f"  {name:8s}: {count:2d}/56 ({pct:5.1f}%)")

print("=" * 130)
