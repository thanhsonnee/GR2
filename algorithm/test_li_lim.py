"""
Batch test for Li & Lim PDPTW Benchmark
Runs ILS+AGES+LNS+LAHC on ALL Li & Lim pdp100 instances
"""

import os
import time
import json
import glob
from typing import Dict, List
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from feasibility_validator import validate_solution
from bks_li_lim import get_bks, calculate_gap


# Li & Lim pdp100 directory
LI_LIM_DIR = "../instances/pdp_100"

# Time limit per instance (HARD LIMIT)
TIME_LIMIT_PER_INSTANCE = 30  # seconds (improved quality for better BKS gaps)


import random
import argparse

class LiLimTester:
    """Batch tester for Li & Lim PDPTW benchmark"""
    
    def __init__(self, seed: int = None, runs: int = 1):
        self.results = []
        self.total_instances = 0
        self.feasible_count = 0
        self.infeasible_count = 0
        self.failed_count = 0
        self.seed = seed
        self.runs = runs
        
        if self.seed is not None:
            print(f"Global Random Seed: {self.seed}")
            self.set_seed(self.seed)
            
    def set_seed(self, seed: int):
        """Set random seed for reproducibility"""
        random.seed(seed)
        # np.random.seed(seed) # If numpy is used later
    
    def run_all_instances(self):
        """Run on ALL Li & Lim pdp100 instances"""
        print("="*80)
        print("LI & LIM PDPTW BENCHMARK - FULL RUN")
        print("="*80)
        
        # Get all instance files
        instance_files = self._get_li_lim_instances()
        
        if not instance_files:
            print("ERROR: No Li & Lim instances found!")
            print(f"Expected directory: {LI_LIM_DIR}")
            return
        
        print(f"Found {len(instance_files)} instances in {LI_LIM_DIR}")
        print(f"Time limit: {TIME_LIMIT_PER_INSTANCE}s per instance")
        print(f"Algorithm: ILS + AGES + LNS + LAHC (strict feasibility)")
        if self.runs > 1:
            print(f"Configuration: Best of {self.runs} runs per instance")
        if self.seed is not None:
            print(f"Reproducibility: Fixed Seed {self.seed}")
        print("="*80)
        
        # Process each instance
        start_time_total = time.time()
        
        for i, instance_file in enumerate(instance_files, 1):
            instance_name = os.path.basename(instance_file)
            
            print(f"\n[{i}/{len(instance_files)}] {instance_name}")
            print("-"*80)
            
            # If seed matches level 1 (fixed seed), we want deterministic sequence
            # But if runs > 1, we might want different seeds for each run?
            # Strategy: If global seed set, re-seed before each instance to ensure
            # skipping an instance doesn't affect others if we were to implement partial runs.
            # For now, just rely on global stream or set specific seed per instance.
            
            best_result = None
            
            for run in range(1, self.runs + 1):
                if self.runs > 1:
                    print(f"  Run {run}/{self.runs}...")
                
                # If doing multiple runs without a fixed global seed, we let it be random.
                # If doing multiple runs WITH a fixed global seed, we want diversity but deterministic.
                # So we can seed with (global_seed + instance_idx + run_idx)
                if self.seed is not None and self.runs > 1:
                    run_seed = self.seed + i * 1000 + run
                    self.set_seed(run_seed)
                
                result = self._test_single_instance(instance_file)
                
                # Logic to keep best result
                if best_result is None:
                    best_result = result
                else:
                    # Prefer Feasible over Infeasible
                    if result['feasible'] and not best_result['feasible']:
                        best_result = result
                    elif result['feasible'] and best_result['feasible']:
                        # Prefer fewer vehicles
                        if result['vehicles'] < best_result['vehicles']:
                            best_result = result
                        elif result['vehicles'] == best_result['vehicles']:
                            # Prefer lower cost
                            if result['cost'] < best_result['cost']:
                                best_result = result
            
            self.results.append(best_result)
            
            # Update counters based on BEST result
            self.total_instances += 1
            if best_result['feasible']:
                self.feasible_count += 1
            elif best_result['status'] == 'FAILED':
                self.failed_count += 1
            else:
                self.infeasible_count += 1
            
            # Progress indicator
            elapsed_total = time.time() - start_time_total
            avg_time = elapsed_total / (i)
            eta = avg_time * (len(instance_files) - i)
            print(f"Progress: {i}/{len(instance_files)} | "
                  f"Feasible: {self.feasible_count} | "
                  f"ETA: {eta/60:.1f} min")
        
        total_runtime = time.time() - start_time_total
        
        # Generate summary
        self._print_summary(total_runtime)
        
        # Save results
        self._save_results()
    
    def _get_li_lim_instances(self) -> List[str]:
        """Get all Li & Lim instance files from pdp_100 directory"""
        if not os.path.exists(LI_LIM_DIR):
            return []
        
        # Get all .txt files in the directory
        pattern = os.path.join(LI_LIM_DIR, "*.txt")
        instance_files = glob.glob(pattern)
        
        # Sort by class (lc, lr, lrc) then by number
        def sort_key(path):
            name = os.path.basename(path)
            # Extract class (lc/lr/lrc) and number
            if name.startswith('lrc'):
                class_name = 'lrc'
                num = name[3:-4]  # Remove 'lrc' and '.txt'
            elif name.startswith('lr'):
                class_name = 'lr'
                num = name[2:-4]
            elif name.startswith('lc'):
                class_name = 'lc'
                num = name[2:-4]
            else:
                class_name = 'zzz'
                num = '999'
            
            try:
                return (class_name, int(num))
            except:
                return (class_name, 999)
        
        instance_files.sort(key=sort_key)
        return instance_files
    
    def _test_single_instance(self, instance_file: str) -> Dict:
        """Test a single instance"""
        instance_name = os.path.basename(instance_file).replace('.txt', '')
        
        # Infer class from filename
        if instance_name.startswith('lrc'):
            instance_class = 'LRC'
        elif instance_name.startswith('lr'):
            instance_class = 'LR'
        elif instance_name.startswith('lc'):
            instance_class = 'LC'
        else:
            instance_class = 'UNKNOWN'
        
        try:
            # Load instance
            instance = Instance()
            instance.read_from_file(instance_file)
            
            print(f"  Class: {instance_class}")
            print(f"  Size: {instance.size} nodes, Capacity: {instance.capacity}")
            
            # Run ILS
            start_time = time.time()
            ils = IteratedLocalSearch(
                instance,
                max_iterations=20,  # Reduced (focus on LNS quality instead)
                max_time=TIME_LIMIT_PER_INSTANCE
            )
            
            ils_result = ils.solve()
            runtime = time.time() - start_time
            
            # Check if ILS succeeded
            if ils_result is None:
                print(f"  [FAILED] Could not find feasible solution")
                bks = get_bks(instance_name)
                return {
                    'instance': instance_name,
                    'class': instance_class,
                    'status': 'FAILED',
                    'feasible': False,
                    'vehicles': -1,
                    'cost': -1,
                    'runtime': runtime,
                    'bks_vehicles': bks['vehicles'] if bks else None,
                    'bks_cost': bks['cost'] if bks else None,
                    'gap_vehicles': 0.0,
                    'gap_cost': 0.0
                }
            
            # Extract results
            vehicles = ils_result.get('vehicles', -1)
            cost = ils_result.get('cost', -1)
            is_feasible = ils_result.get('is_feasible', False)
            
            # Get BKS and calculate gaps
            bks = get_bks(instance_name)
            if bks:
                bks_vehicles = bks['vehicles']
                bks_cost = bks['cost']
                gap_vehicles = calculate_gap(vehicles, bks_vehicles)
                gap_cost = calculate_gap(cost, bks_cost)
            else:
                bks_vehicles = None
                bks_cost = None
                gap_vehicles = 0.0
                gap_cost = 0.0
            
            # Log result
            status = 'FEASIBLE' if is_feasible else 'INFEASIBLE'
            symbol = '[OK]' if is_feasible else '[X]'
            
            print(f"  {symbol} {status}: {vehicles} veh, cost {cost:.0f}, time {runtime:.1f}s")
            if bks:
                print(f"      BKS: {bks_vehicles} veh, {bks_cost:.2f} cost")
                print(f"      GAP: {gap_vehicles:+.1f}% (veh), {gap_cost:+.1f}% (cost)")
            
            return {
                'instance': instance_name,
                'class': instance_class,
                'status': status,
                'feasible': is_feasible,
                'vehicles': vehicles,
                'cost': cost,
                'runtime': runtime,
                'bks_vehicles': bks_vehicles,
                'bks_cost': bks_cost,
                'gap_vehicles': gap_vehicles,
                'gap_cost': gap_cost
            }
            
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            import traceback
            traceback.print_exc()
            
            bks = get_bks(instance_name)
            return {
                'instance': instance_name,
                'class': instance_class,
                'status': 'ERROR',
                'feasible': False,
                'vehicles': -1,
                'cost': -1,
                'runtime': 0,
                'error': str(e),
                'bks_vehicles': bks['vehicles'] if bks else None,
                'bks_cost': bks['cost'] if bks else None,
                'gap_vehicles': 0.0,
                'gap_cost': 0.0
            }
    
    def _print_summary(self, total_runtime: float):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("SUMMARY - LI & LIM PDPTW BENCHMARK")
        print("="*80)
        
        print(f"\nTotal instances: {self.total_instances}")
        print(f"Feasible solutions: {self.feasible_count}/{self.total_instances} "
              f"({100*self.feasible_count/max(self.total_instances,1):.1f}%)")
        print(f"Infeasible solutions: {self.infeasible_count}/{self.total_instances}")
        print(f"Failed/Errors: {self.failed_count}/{self.total_instances}")
        print(f"Total runtime: {total_runtime/60:.1f} minutes")
        
        # Group by class
        feasible_results = [r for r in self.results if r['feasible']]
        
        if feasible_results:
            # Group by class
            by_class = {}
            for r in feasible_results:
                cls = r['class']
                if cls not in by_class:
                    by_class[cls] = []
                by_class[cls].append(r)
            
            print(f"\n{'Class':<8} {'Count':<8} {'Avg Veh':<10} {'Avg Cost':<12} {'Gap_V%':<10} {'Gap_C%':<10} {'Time(s)':<10}")
            print("-"*80)
            
            for cls in sorted(by_class.keys()):
                results = by_class[cls]
                count = len(results)
                avg_veh = sum(r['vehicles'] for r in results) / count
                avg_cost = sum(r['cost'] for r in results) / count
                avg_gap_veh = sum(r.get('gap_vehicles', 0) for r in results) / count
                avg_gap_cost = sum(r.get('gap_cost', 0) for r in results) / count
                avg_time = sum(r['runtime'] for r in results) / count
                
                print(f"{cls:<8} {count:<8} {avg_veh:<10.1f} {avg_cost:<12.1f} {avg_gap_veh:<10.1f} {avg_gap_cost:<10.1f} {avg_time:<10.1f}")
            
            # Overall averages
            print("-"*80)
            overall_gap_veh = sum(r.get('gap_vehicles', 0) for r in feasible_results)/len(feasible_results)
            overall_gap_cost = sum(r.get('gap_cost', 0) for r in feasible_results)/len(feasible_results)
            print(f"{'OVERALL':<8} {len(feasible_results):<8} "
                  f"{sum(r['vehicles'] for r in feasible_results)/len(feasible_results):<10.1f} "
                  f"{sum(r['cost'] for r in feasible_results)/len(feasible_results):<12.1f} "
                  f"{overall_gap_veh:<10.1f} {overall_gap_cost:<10.1f} "
                  f"{sum(r['runtime'] for r in feasible_results)/len(feasible_results):<10.1f}")
        
        # Failed instances
        failed = [r for r in self.results if not r['feasible']]
        if failed:
            print(f"\nFailed/Infeasible instances ({len(failed)}):")
            for r in failed[:10]:  # Show first 10
                print(f"  - {r['instance']}: {r['status']}")
            if len(failed) > 10:
                print(f"  ... and {len(failed)-10} more")
        
        print("="*80)
    
    def _save_results(self):
        """Save results to JSON and CSV"""
        # Save JSON
        json_file = "li_lim_results.json"
        try:
            with open(json_file, 'w') as f:
                json.dump({
                    'benchmark': 'Li & Lim PDPTW pdp100',
                    'time_limit': TIME_LIMIT_PER_INSTANCE,
                    'summary': {
                        'total': self.total_instances,
                        'feasible': self.feasible_count,
                        'infeasible': self.infeasible_count,
                        'failed': self.failed_count
                    },
                    'results': self.results
                }, f, indent=2)
            print(f"\nResults saved to: {json_file}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
        
        # Save CSV
        csv_file = "li_lim_results.csv"
        try:
            with open(csv_file, 'w') as f:
                # Header
                f.write("Instance,Class,Status,Feasible,Vehicles,Cost,Runtime_s,BKS_Veh,BKS_Cost,Gap_Veh_%,Gap_Cost_%\n")
                
                # Data rows
                for r in self.results:
                    bks_veh = r.get('bks_vehicles', '')
                    bks_cost = r.get('bks_cost', '')
                    gap_veh = r.get('gap_vehicles', 0.0)
                    gap_cost = r.get('gap_cost', 0.0)
                    
                    f.write(f"{r['instance']},{r['class']},{r['status']},"
                           f"{r['feasible']},{r['vehicles']},{r['cost']:.2f},{r['runtime']:.2f},"
                           f"{bks_veh},{bks_cost},{gap_veh:.2f},{gap_cost:.2f}\n")
            
            print(f"Results saved to: {csv_file}")
        except Exception as e:
            print(f"Error saving CSV: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Li & Lim PDPTW Benchmark Runner')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility (Level 1)')
    parser.add_argument('--runs', type=int, default=1, help='Number of runs per instance (Level 2)')
    
    args = parser.parse_args()
    
    tester = LiLimTester(seed=args.seed, runs=args.runs)
    tester.run_all_instances()


if __name__ == "__main__":
    main()
