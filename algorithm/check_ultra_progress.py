"""Check progress of ultra aggressive test"""
import json
import os

if os.path.exists('ultra_aggressive_results.json'):
    with open('ultra_aggressive_results.json', 'r') as f:
        results = json.load(f)
    
    total = 29  # lc101-109 + lr101-112 + lrc101-108
    completed = len(results)
    
    print("=" * 80)
    print("ULTRA AGGRESSIVE TEST PROGRESS (WITH ROUTE IMPROVEMENT)")
    print("=" * 80)
    print(f"Completed: {completed}/{total} instances ({100*completed/total:.1f}%)")
    
    if results:
        feasible = sum(1 for r in results if r.get('feasible', True))
        print(f"Feasible: {feasible}/{completed} ({100*feasible/completed:.1f}%)")
        
        # Gap analysis
        gaps = [r['gap_distance'] for r in results if r.get('feasible', True)]
        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            min_gap = min(gaps)
            
            excellent = sum(1 for g in gaps if g <= 5)
            very_good = sum(1 for g in gaps if 5 < g <= 10)
            good = sum(1 for g in gaps if 10 < g <= 20)
            acceptable = sum(1 for g in gaps if 20 < g <= 30)
            
            print(f"\nGap statistics:")
            print(f"  Average: {avg_gap:.1f}% (Target: 20-25%)")
            print(f"  Best: {min_gap:.1f}%")
            print(f"  <=5%: {excellent}/{len(gaps)} ({100*excellent/len(gaps):.1f}%) - Target: 2-5")
            print(f"  <=10%: {excellent+very_good}/{len(gaps)} ({100*(excellent+very_good)/len(gaps):.1f}%)")
            print(f"  <=20%: {excellent+very_good+good}/{len(gaps)} ({100*(excellent+very_good+good)/len(gaps):.1f}%)")
            print(f"  <=30%: {excellent+very_good+good+acceptable}/{len(gaps)}")
            
            # Target check
            print(f"\nTarget achievement (so far):")
            if avg_gap <= 25:
                print(f"  Average gap <=25%: YES ({avg_gap:.1f}%)")
            else:
                print(f"  Average gap <=25%: NO ({avg_gap:.1f}%)")
            
            if excellent >= 2:
                print(f"  Gap <=5% for 2-5 instances: YES ({excellent} instances)")
            else:
                print(f"  Gap <=5% for 2-5 instances: NO ({excellent} instances)")
        
        # Last tested
        if results:
            last = results[-1]
            print(f"\nLast tested: {last['instance']}")
            print(f"  Result: {last['vehicles']} veh, {last['distance']:.0f} dist")
            print(f"  BKS: {last['bks_vehicles']} veh, {last['bks_distance']:.2f} dist")
            print(f"  Gap: {last['gap_distance']:+.1f}%")
            print(f"  Time: {last['runtime']:.1f}s")
            
            if last['gap_distance'] <= 5:
                print(f"  >>> EXCELLENT! <<<")
            elif last['gap_distance'] <= 10:
                print(f"  >> VERY GOOD <<")
            elif last['gap_distance'] <= 25:
                print(f"  > ON TARGET <")
    
    # Estimate remaining
    if completed > 0 and completed < total:
        avg_time = sum(r['runtime'] for r in results) / len(results)
        remaining_time = (total - completed) * avg_time
        print(f"\nEstimated remaining: {remaining_time/60:.1f} minutes")
    
    print("=" * 80)
else:
    print("=" * 80)
    print("Ultra test not started yet or still initializing...")
    print("This is normal - constructing initial solution can take 2-3 minutes.")
    print("=" * 80)
