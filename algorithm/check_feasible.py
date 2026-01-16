"""Simple script to check feasibility from JSON results"""
import json
import os

# Check Li & Lim results
if os.path.exists('li_lim_results.json'):
    print("="*60)
    print("LI & LIM RESULTS")
    print("="*60)
    with open('li_lim_results.json') as f:
        data = json.load(f)
    
    total = data['summary']['total']
    feasible = data['summary']['feasible']
    infeasible = data['summary']['infeasible']
    failed = data['summary']['failed']
    
    print(f"Total instances: {total}")
    print(f"Feasible: {feasible}/{total} ({100*feasible/total:.1f}%)")
    print(f"Infeasible: {infeasible}/{total}")
    print(f"Failed: {failed}/{total}")
    
    if feasible == total:
        print("\nALL FEASIBLE - PERFECT!")
    else:
        print(f"\nSTILL {total-feasible} INFEASIBLE INSTANCES")
        
        # Show problematic instances
        print("\nProblematic instances:")
        for r in data['results']:
            if not r.get('feasible', False):
                print(f"  - {r['instance']}: {r['status']}")
    
    print("="*60)
else:
    print("No li_lim_results.json file found")
    print("Run: python test_li_lim.py")

# Check Sartori results
if os.path.exists('feasibility_test_results.json'):
    print("\n" + "="*60)
    print("SARTORI & BURIOL RESULTS")
    print("="*60)
    with open('feasibility_test_results.json') as f:
        data = json.load(f)
    
    total = data['summary']['total']
    feasible = data['summary']['feasible']
    
    print(f"Total instances: {total}")
    print(f"Feasible: {feasible}/{total}")
    
    if feasible == total:
        print("ALL FEASIBLE!")
    else:
        print(f"STILL {total-feasible} INFEASIBLE")
    
    print("="*60)
