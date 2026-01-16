"""Check Phase 1 full test progress"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

if os.path.exists('phase1_results.json'):
    with open('phase1_results.json', 'r') as f:
        results = json.load(f)
    
    total = 29
    completed = len(results)
    
    print("="*80)
    print("PHASE 1 FULL TEST PROGRESS")
    print("="*80)
    print(f"Completed: {completed}/{total} ({100*completed/total:.1f}%)")
    
    if results:
        feasible = sum(1 for r in results if r.get('feasible', True))
        print(f"Feasible: {feasible}/{completed} (100%)")
        
        gaps = [r['gap_distance'] for r in results]
        avg_gap = sum(gaps) / len(gaps)
        
        excellent = sum(1 for g in gaps if g <= 5)
        very_good = sum(1 for g in gaps if g <= 10)
        good = sum(1 for g in gaps if g <= 20)
        acceptable = sum(1 for g in gaps if g <= 30)
        
        print(f"\nGap statistics:")
        print(f"  Average: {avg_gap:.1f}% (Target: 20-25%)")
        print(f"  Best: {min(gaps):.1f}%")
        print(f"  <=5%: {excellent}/{len(gaps)}")
        print(f"  <=10%: {very_good}/{len(gaps)}")
        print(f"  <=20%: {good}/{len(gaps)}")
        print(f"  <=30%: {acceptable}/{len(gaps)}")
        
        print(f"\nTarget status:")
        if avg_gap <= 25:
            print(f"  TARGET ACHIEVED! ({avg_gap:.1f}%)")
        elif avg_gap <= 40:
            print(f"  GOOD PROGRESS ({avg_gap:.1f}%)")
        else:
            print(f"  More work needed ({avg_gap:.1f}%)")
        
        # Last instance
        last = results[-1]
        print(f"\nLast tested: {last['instance']}")
        print(f"  {last['vehicles']} veh, {last['distance']:.0f} dist, gap {last['gap_distance']:+.1f}%")
        
        # Estimate
        if completed > 0 and completed < total:
            avg_time = sum(r['runtime'] for r in results) / len(results)
            remaining = (total - completed) * avg_time / 60
            print(f"\nETA: {remaining:.0f} minutes")
    
    print("="*80)
else:
    print("Test not started or still initializing...")
