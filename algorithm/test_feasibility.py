"""
Simple batch test for ILS framework - Focus on FEASIBILITY and STABILITY
Runs on a SMALL fixed set of instances with detailed logging
"""

import os
import time
import json
from typing import Dict, List
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch
from feasibility_validator import validate_solution


# FIXED TEST SET - Small instances only
TEST_INSTANCES = [
    "../instances/n100/n100/bar-n100-1.txt",
    "../instances/n100/n100/bar-n100-2.txt",
    "../instances/n100/n100/bar-n100-3.txt",
]

# Conservative time limit per instance
TIME_LIMIT_PER_INSTANCE = 60  # seconds


class FeasibilityTester:
    """Batch tester focused on feasibility and stability"""
    
    def __init__(self):
        self.results = []
        self.total_instances = 0
        self.feasible_count = 0
        self.infeasible_count = 0
        self.failed_count = 0
    
    def run_tests(self):
        """Run batch tests on fixed instance set"""
        print("="*80)
        print("FEASIBILITY-FOCUSED BATCH TEST")
        print("="*80)
        print(f"Testing {len(TEST_INSTANCES)} instances")
        print(f"Time limit: {TIME_LIMIT_PER_INSTANCE}s per instance")
        print(f"Priority: FEASIBILITY > Performance")
        print("="*80)
        
        for i, instance_file in enumerate(TEST_INSTANCES, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(TEST_INSTANCES)}] Testing: {os.path.basename(instance_file)}")
            print(f"{'='*80}")
            
            result = self._test_single_instance(instance_file)
            self.results.append(result)
            
            # Update counters
            self.total_instances += 1
            if result['status'] == 'FEASIBLE':
                self.feasible_count += 1
            elif result['status'] == 'INFEASIBLE':
                self.infeasible_count += 1
            else:
                self.failed_count += 1
        
        # Generate summary
        self._print_summary()
        
        # Save results to JSON
        self._save_results()
    
    def _test_single_instance(self, instance_file: str) -> Dict:
        """Test a single instance and return detailed results"""
        instance_name = os.path.basename(instance_file)
        
        try:
            # Load instance
            instance = Instance()
            instance.read_from_file(instance_file)
            
            print(f"Instance size: {instance.size} nodes, capacity: {instance.capacity}")
            print(f"Pickup-delivery pairs: {len(instance.get_pickup_delivery_pairs())}")
            
            # Run ILS
            start_time = time.time()
            ils = IteratedLocalSearch(
                instance,
                max_iterations=10,  # Conservative
                max_time=TIME_LIMIT_PER_INSTANCE
            )
            
            ils_result = ils.solve()
            runtime = time.time() - start_time
            
            # Check if ILS succeeded
            if ils_result is None:
                return {
                    'instance': instance_name,
                    'status': 'FAILED',
                    'failure_reason': 'ILS returned None (could not find feasible solution)',
                    'runtime': runtime,
                    'vehicles': -1,
                    'cost': -1,
                    'is_feasible': False
                }
            
            # Get solution details
            vehicles = ils_result.get('vehicles', -1)
            cost = ils_result.get('cost', -1)
            is_feasible = ils_result.get('is_feasible', False)
            gap_vehicles = ils_result.get('gap_vehicles', 0.0)
            gap_cost = ils_result.get('gap_cost', 0.0)
            best_vehicles = ils_result.get('best_vehicles', -1)
            best_cost = ils_result.get('best_cost', -1)
            
            # Determine status
            if is_feasible:
                status = 'FEASIBLE'
                status_symbol = '[OK]'
            else:
                status = 'INFEASIBLE'
                status_symbol = '[X]'
            
            # Print result
            print(f"\n{status_symbol} RESULT:")
            print(f"  Status: {status}")
            print(f"  Vehicles: {vehicles} (Best known: {best_vehicles})")
            print(f"  Cost: {cost} (Best known: {best_cost})")
            print(f"  Gap (vehicles): {gap_vehicles:.2f}%")
            print(f"  Gap (cost): {gap_cost:.2f}%")
            print(f"  Runtime: {runtime:.2f}s")
            
            return {
                'instance': instance_name,
                'status': status,
                'vehicles': vehicles,
                'cost': cost,
                'is_feasible': is_feasible,
                'gap_vehicles': gap_vehicles,
                'gap_cost': gap_cost,
                'best_vehicles': best_vehicles,
                'best_cost': best_cost,
                'runtime': runtime
            }
            
        except FileNotFoundError:
            print(f"[ERROR] Instance file not found: {instance_file}")
            return {
                'instance': instance_name,
                'status': 'ERROR',
                'failure_reason': 'File not found',
                'runtime': 0,
                'vehicles': -1,
                'cost': -1,
                'is_feasible': False
            }
        
        except Exception as e:
            print(f"[ERROR] Exception during test: {e}")
            import traceback
            traceback.print_exc()
            return {
                'instance': instance_name,
                'status': 'ERROR',
                'failure_reason': str(e),
                'runtime': 0,
                'vehicles': -1,
                'cost': -1,
                'is_feasible': False
            }
    
    def _print_summary(self):
        """Print summary of all tests"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        print(f"\nTotal instances tested: {self.total_instances}")
        print(f"Feasible solutions: {self.feasible_count}/{self.total_instances} "
              f"({100*self.feasible_count/max(self.total_instances,1):.1f}%)")
        print(f"Infeasible solutions: {self.infeasible_count}/{self.total_instances}")
        print(f"Failed/Errors: {self.failed_count}/{self.total_instances}")
        
        # Detailed results table
        feasible_results = [r for r in self.results if r.get('is_feasible', False)]
        
        if feasible_results:
            print(f"\n{'Instance':<20} {'Vehicles':<10} {'Cost':<10} {'Gap_V(%)':<10} {'Gap_C(%)':<10} {'Time(s)':<10}")
            print("-"*80)
            
            for result in feasible_results:
                print(f"{result['instance']:<20} "
                      f"{result['vehicles']:<10} "
                      f"{result['cost']:<10} "
                      f"{result.get('gap_vehicles', 0):<10.2f} "
                      f"{result.get('gap_cost', 0):<10.2f} "
                      f"{result['runtime']:<10.1f}")
            
            avg_gap_v = sum(r.get('gap_vehicles', 0) for r in feasible_results) / len(feasible_results)
            avg_gap_c = sum(r.get('gap_cost', 0) for r in feasible_results) / len(feasible_results)
            avg_time = sum(r.get('runtime', 0) for r in feasible_results) / len(feasible_results)
            
            print("-"*80)
            print(f"{'AVERAGE':<20} {'-':<10} {'-':<10} "
                  f"{avg_gap_v:<10.2f} {avg_gap_c:<10.2f} {avg_time:<10.1f}")
        
        # Failed instances
        failed_results = [r for r in self.results if not r.get('is_feasible', False)]
        if failed_results:
            print(f"\nFailed/Infeasible instances:")
            for result in failed_results:
                reason = result.get('failure_reason', 'Infeasible')
                print(f"  - {result['instance']}: {result['status']} ({reason})")
        
        print("="*80)
    
    def _save_results(self):
        """Save results to JSON file"""
        output_file = "feasibility_test_results.json"
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total': self.total_instances,
                        'feasible': self.feasible_count,
                        'infeasible': self.infeasible_count,
                        'failed': self.failed_count
                    },
                    'results': self.results
                }, f, indent=2)
            print(f"\nResults saved to: {output_file}")
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """Main entry point"""
    tester = FeasibilityTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
