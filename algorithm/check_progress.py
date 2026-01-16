"""
Quick script to check test progress
"""
import os
import time

results_file = "li_lim_results.json"

print("Checking test progress...")
print("=" * 60)

if os.path.exists(results_file):
    import json
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    total = data['summary']['total']
    feasible = data['summary']['feasible']
    
    print(f"Completed: {len(results)}/56 instances")
    print(f"Feasible: {feasible}/{len(results)} ({100*feasible/max(len(results),1):.1f}%)")
    
    if results:
        last = results[-1]
        print(f"\nLast tested: {last['instance']}")
        print(f"  Result: {last['vehicles']} veh, {last['cost']:.0f} cost")
        if last.get('bks_vehicles'):
            print(f"  BKS: {last['bks_vehicles']} veh, {last['bks_cost']:.2f} cost")
            print(f"  Gap: {last['gap_vehicles']:+.1f}% (veh), {last['gap_cost']:+.1f}% (cost)")
else:
    print("Test not started yet or results file not created")
    print("Please wait a few seconds...")

print("=" * 60)
