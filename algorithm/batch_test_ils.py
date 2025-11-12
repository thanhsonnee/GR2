"""
Batch testing script for ILS framework
Tests multiple instances and generates comparison table
"""

import os
import time
import json
from typing import Dict, List
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch


class BatchTester:
    """Batch testing framework for ILS algorithm"""
    
    def __init__(self, instances_dir: str = "../instances/n100/n100/", 
                 results_file: str = "ils_batch_results.json"):
        self.instances_dir = instances_dir
        self.results_file = results_file
        self.results = []
    
    def run_batch_test(self, max_instances: int = 10, max_time_per_instance: int = 120):
        """Run ILS on multiple instances"""
        print("="*80)
        print("BATCH TESTING - ILS FRAMEWORK FOR PDPTW")
        print("="*80)
        
        # Get instance files
        instance_files = self._get_instance_files(max_instances)
        
        if not instance_files:
            print("No instance files found!")
            return
        
        print(f"Testing on {len(instance_files)} instances...")
        print(f"Max time per instance: {max_time_per_instance}s")
        print("-"*80)
        
        for i, instance_file in enumerate(instance_files, 1):
            print(f"\n[{i}/{len(instance_files)}] Testing instance: {os.path.basename(instance_file)}")
            
            try:
                # Load instance
                instance = Instance()
                instance.read_from_file(instance_file)
                
                # Run ILS
                start_time = time.time()
                ils = IteratedLocalSearch(
                    instance, 
                    max_iterations=5, 
                    max_time=max_time_per_instance
                )
                result = ils.solve()
                runtime = time.time() - start_time
                
                # Store result
                result['runtime'] = runtime
                result['instance_file'] = instance_file
                self.results.append(result)
                
                # Print summary
                print(f"[OK] {result['instance']}: {result['vehicles']} veh, cost={result['cost']}, "
                      f"gapv={result['gap_vehicles']:.2f}%, gapc={result['gap_cost']:.2f}%")
                
            except Exception as e:
                print(f"[ERROR] Error testing {instance_file}: {e}")
                continue
        
        # Save results
        self._save_results()
        
        # Generate comparison table
        self._generate_comparison_table()
        
        print("\n" + "="*80)
        print("BATCH TESTING COMPLETED")
        print("="*80)
    
    def _get_instance_files(self, max_instances: int) -> List[str]:
        """Get list of instance files to test"""
        instance_files = []
        
        if os.path.exists(self.instances_dir):
            for file in os.listdir(self.instances_dir):
                if file.endswith('.txt'):
                    instance_files.append(os.path.join(self.instances_dir, file))
                    
                    if len(instance_files) >= max_instances:
                        break
        
        # Also try single instance files
        single_instances = [
            "../instances/bar-n100-1.txt",
            "../instances/nyc-n100-1.txt"
        ]
        
        for file in single_instances:
            if os.path.exists(file) and len(instance_files) < max_instances:
                instance_files.append(file)
        
        return sorted(instance_files)[:max_instances]
    
    def _save_results(self):
        """Save results to JSON file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\nResults saved to: {self.results_file}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def _generate_comparison_table(self):
        """Generate comparison table similar to research paper"""
        if not self.results:
            print("No results to display")
            return
        
        print("\n" + "="*100)
        print("RESULTS COMPARISON TABLE")
        print("="*100)
        
        # Table header
        header = f"{'Instance':<15} {'Veh.':<5} {'Cost':<8} {'gapv(%)':<8} {'gapc(%)':<8} {'Time(s)':<8} {'BK_Veh':<7} {'BK_Cost':<8}"
        print(header)
        print("-"*100)
        
        # Results rows
        total_instances = len(self.results)
        avg_gap_vehicles = 0
        avg_gap_cost = 0
        avg_time = 0
        
        for result in self.results:
            instance_name = result['instance'][:14]  # Truncate long names
            vehicles = result['vehicles']
            cost = int(result['cost'])
            gap_vehicles = result['gap_vehicles']
            gap_cost = result['gap_cost']
            runtime = result['runtime']
            bk_vehicles = result.get('best_vehicles', '-')
            bk_cost = int(result.get('best_cost', 0)) if result.get('best_cost') else '-'
            
            row = f"{instance_name:<15} {vehicles:<5} {cost:<8} {gap_vehicles:<8.2f} {gap_cost:<8.2f} {runtime:<8.1f} {bk_vehicles:<7} {bk_cost:<8}"
            print(row)
            
            avg_gap_vehicles += gap_vehicles
            avg_gap_cost += gap_cost
            avg_time += runtime
        
        # Summary
        print("-"*100)
        avg_gap_vehicles /= total_instances
        avg_gap_cost /= total_instances
        avg_time /= total_instances
        
        summary = f"{'AVERAGE':<15} {'-':<5} {'-':<8} {avg_gap_vehicles:<8.2f} {avg_gap_cost:<8.2f} {avg_time:<8.1f} {'-':<7} {'-':<8}"
        print(summary)
        
        print("\n" + "="*100)
        print("SUMMARY STATISTICS")
        print("="*100)
        print(f"Total instances tested: {total_instances}")
        print(f"Average vehicle gap: {avg_gap_vehicles:.2f}%")
        print(f"Average cost gap: {avg_gap_cost:.2f}%")
        print(f"Average runtime: {avg_time:.1f}s")
        
        # Best results
        best_vehicle_gap = min(r['gap_vehicles'] for r in self.results)
        best_cost_gap = min(r['gap_cost'] for r in self.results)
        
        print(f"Best vehicle gap: {best_vehicle_gap:.2f}%")
        print(f"Best cost gap: {best_cost_gap:.2f}%")
        
        # Count improvements
        improvements = sum(1 for r in self.results if r['gap_vehicles'] < 0 or r['gap_cost'] < 0)
        print(f"Instances with improvements: {improvements}/{total_instances} ({100*improvements/total_instances:.1f}%)")


def main():
    """Main function to run batch testing"""
    # Create batch tester
    tester = BatchTester()
    
    # Run batch test on available instances
    tester.run_batch_test(max_instances=8, max_time_per_instance=90)


if __name__ == "__main__":
    main()
