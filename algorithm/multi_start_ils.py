"""
Multi-Start ILS - Run multiple independent trials and select best
==================================================================
Key improvement: Diversification through multiple random seeds
"""

import random
import time
from typing import Dict, Optional
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch


class MultiStartILS:
    """
    Multi-start wrapper for ILS
    
    Runs N independent trials with different random seeds,
    selects best result based on lexicographic (vehicles, distance) ordering
    """
    
    def __init__(self, instance: Instance, num_trials: int = 15, 
                 time_per_trial: int = 20):
        """
        Args:
            instance: PDPTW instance
            num_trials: Number of independent trials (10-30 recommended)
            time_per_trial: Time limit per trial in seconds
        """
        self.instance = instance
        self.num_trials = num_trials
        self.time_per_trial = time_per_trial
        
    def solve(self) -> Optional[Dict]:
        """
        Run multi-start ILS
        
        Returns:
            Best solution found across all trials
        """
        print("="*80)
        print(f"MULTI-START ILS")
        print("="*80)
        print(f"Trials: {self.num_trials}")
        print(f"Time per trial: {self.time_per_trial}s")
        print(f"Total time budget: {self.num_trials * self.time_per_trial}s")
        print("="*80)
        
        best_solution = None
        best_score = (float('inf'), float('inf'))  # (vehicles, distance)
        
        trial_results = []
        
        for trial in range(1, self.num_trials + 1):
            print(f"\n--- Trial {trial}/{self.num_trials} ---")
            
            # Set random seed for reproducibility and diversity
            seed = 1000 * trial + int(time.time()) % 1000
            random.seed(seed)
            
            # Run ILS with limited time
            try:
                ils = IteratedLocalSearch(
                    self.instance,
                    max_iterations=10,  # Fewer iterations, more trials
                    max_time=self.time_per_trial,
                    no_improvement_limit=999
                )
                
                result = ils.solve()
                
                if result is not None:
                    vehicles = result['vehicles']
                    distance = result['cost']
                    feasible = result.get('feasible', True)
                    
                    score = (vehicles, distance)
                    
                    print(f"Trial {trial} result: {vehicles} veh, {distance:.0f} dist, feasible={feasible}")
                    
                    # Update best if this is better (lexicographic)
                    if feasible and score < best_score:
                        best_score = score
                        best_solution = result
                        print(f"  >>> NEW BEST! <<<")
                    
                    trial_results.append({
                        'trial': trial,
                        'vehicles': vehicles,
                        'distance': distance,
                        'feasible': feasible
                    })
                else:
                    print(f"Trial {trial} FAILED")
                    
            except Exception as e:
                print(f"Trial {trial} ERROR: {e}")
                continue
        
        # Summary
        print(f"\n{'='*80}")
        print(f"MULTI-START SUMMARY")
        print(f"{'='*80}")
        
        if trial_results:
            print(f"Successful trials: {len(trial_results)}/{self.num_trials}")
            
            # Show distribution
            vehicles_list = [r['vehicles'] for r in trial_results if r['feasible']]
            if vehicles_list:
                print(f"Vehicles range: {min(vehicles_list)} - {max(vehicles_list)}")
                print(f"Best result: {best_score[0]} veh, {best_score[1]:.0f} dist")
                
                # Count unique vehicle counts
                from collections import Counter
                veh_counts = Counter(vehicles_list)
                print(f"Vehicle distribution:")
                for veh, count in sorted(veh_counts.items()):
                    print(f"  {veh} vehicles: {count} trial(s)")
        
        print(f"{'='*80}")
        
        return best_solution


def test_multi_start():
    """Quick test on lc101"""
    from data_loader import Instance
    from bks_li_lim import LI_LIM_BKS
    
    print("Testing Multi-Start ILS on lc101")
    
    instance = Instance()
    instance.read_from_file("../instances/pdp_100/lc101.txt")
    
    ms = MultiStartILS(instance, num_trials=5, time_per_trial=15)
    result = ms.solve()
    
    if result:
        bks = LI_LIM_BKS.get('lc101', {})
        bks_veh = bks.get('vehicles', result['vehicles'])
        bks_dist = bks.get('cost', result['cost'])
        
        gap_veh = ((result['vehicles'] - bks_veh) / bks_veh * 100)
        gap_dist = ((result['cost'] - bks_dist) / bks_dist * 100)
        
        print(f"\nFINAL BEST:")
        print(f"  Vehicles: {result['vehicles']} (BKS: {bks_veh}) -> Gap: {gap_veh:+.1f}%")
        print(f"  Distance: {result['cost']:.0f} (BKS: {bks_dist:.2f}) -> Gap: {gap_dist:+.1f}%")


if __name__ == "__main__":
    test_multi_start()
