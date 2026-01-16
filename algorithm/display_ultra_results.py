"""Display ultra aggressive test results with detailed analysis"""
import json
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

with open('ultra_aggressive_results.json', 'r') as f:
    results = json.load(f)

print("=" * 100)
print("ULTRA AGGRESSIVE TEST - DETAILED RESULTS")
print("=" * 100)

# Sort by gap
results_sorted = sorted(results, key=lambda x: x['gap_distance'])

# Top 10 best
print("\n>>> TOP 10 BEST RESULTS:")
print("-" * 100)
print(f"{'Instance':<12} {'Veh':>4} {'BKS_V':>6} {'Distance':>8} {'BKS_Dist':>10} {'Gap_V':>8} {'Gap_D':>8} {'Time':>6}")
print("-" * 100)
for r in results_sorted[:10]:
    gap_v = ((r['vehicles'] - r['bks_vehicles']) / r['bks_vehicles'] * 100) if r['bks_vehicles'] > 0 else 0
    print(f"{r['instance']:<12} {r['vehicles']:>4} {r['bks_vehicles']:>6} {r['distance']:>8.0f} {r['bks_distance']:>10.2f} {gap_v:>7.1f}% {r['gap_distance']:>7.1f}% {r['runtime']:>6.1f}s")

# Top 10 worst
print("\n>>> TOP 10 WORST RESULTS:")
print("-" * 100)
print(f"{'Instance':<12} {'Veh':>4} {'BKS_V':>6} {'Distance':>8} {'BKS_Dist':>10} {'Gap_V':>8} {'Gap_D':>8} {'Time':>6}")
print("-" * 100)
for r in results_sorted[-10:]:
    gap_v = ((r['vehicles'] - r['bks_vehicles']) / r['bks_vehicles'] * 100) if r['bks_vehicles'] > 0 else 0
    print(f"{r['instance']:<12} {r['vehicles']:>4} {r['bks_vehicles']:>6} {r['distance']:>8.0f} {r['bks_distance']:>10.2f} {gap_v:>7.1f}% {r['gap_distance']:>7.1f}% {r['runtime']:>6.1f}s")

# Summary by class
print("\n>>> SUMMARY BY CLASS:")
print("-" * 100)
classes = {}
for r in results:
    cls = r['instance'][:2]  # lc, lr, lrc
    if cls not in classes:
        classes[cls] = []
    classes[cls].append(r)

for cls in sorted(classes.keys()):
    instances = classes[cls]
    avg_gap = sum(i['gap_distance'] for i in instances) / len(instances)
    avg_veh_gap = sum(((i['vehicles'] - i['bks_vehicles']) / i['bks_vehicles'] * 100) for i in instances) / len(instances)
    best_gap = min(i['gap_distance'] for i in instances)
    worst_gap = max(i['gap_distance'] for i in instances)
    
    print(f"{cls.upper()}: {len(instances)} instances")
    print(f"  Avg gap: {avg_gap:.1f}% (veh: {avg_veh_gap:.1f}%)")
    print(f"  Best: {best_gap:.1f}%, Worst: {worst_gap:.1f}%")

# Overall
print("\n>>> OVERALL:")
print("-" * 100)
feasible = sum(1 for r in results if r.get('feasible', True))
avg_gap = sum(r['gap_distance'] for r in results) / len(results)
avg_time = sum(r['runtime'] for r in results) / len(results)

gaps = [r['gap_distance'] for r in results]
under_30 = sum(1 for g in gaps if g <= 30)
under_40 = sum(1 for g in gaps if g <= 40)
under_50 = sum(1 for g in gaps if g <= 50)

print(f"Feasibility: {feasible}/{len(results)} (100%)")
print(f"Average gap: {avg_gap:.1f}% (Target: 20-25%)")
print(f"Best gap: {min(gaps):.1f}%")
print(f"Worst gap: {max(gaps):.1f}%")
print(f"")
print(f"Gap <=30%: {under_30}/{len(results)} ({100*under_30/len(results):.1f}%)")
print(f"Gap <=40%: {under_40}/{len(results)} ({100*under_40/len(results):.1f}%)")
print(f"Gap <=50%: {under_50}/{len(results)} ({100*under_50/len(results):.1f}%)")
print(f"")
print(f"Avg runtime: {avg_time:.1f}s/instance")
print(f"Total time: {sum(r['runtime'] for r in results)/60:.1f} minutes")

print("\n" + "=" * 100)
print("VERDICT: ❌ CHƯA ĐẠT TARGET (gap 76.3% vs target 20-25%)")
print("=" * 100)
