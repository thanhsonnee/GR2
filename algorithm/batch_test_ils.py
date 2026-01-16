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
    
    def __init__(self, instances_dir: str = "../instances/n100/n100", 
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
                result = ils.solve() # Hàm này đang trả về None
                runtime = time.time() - start_time
                
                # --- SỬA ĐỔI BẮT ĐẦU TỪ ĐÂY ---
                if result is None:
                    print(f"[FAILED] Could not find a feasible solution for {instance_file}")
                    # Ghi nhận thất bại để không crash
                    failed_result = {
                        'instance': os.path.basename(instance_file),
                        'vehicles': -1,
                        'cost': -1,
                        'gap_vehicles': 0.0, # Hoặc số khác để đánh dấu
                        'gap_cost': 0.0,
                        'runtime': runtime,
                        'status': 'FAILED'
                    }
                    self.results.append(failed_result)
                    continue # Bỏ qua các bước xử lý kết quả thành công
                
                # Nếu có result thì mới gán thông tin
                result['runtime'] = runtime
                result['instance_file'] = instance_file
                self.results.append(result)
                
                print(f"[OK] {result['instance']}: {result['vehicles']} veh, cost={result['cost']}, "
                      f"gapv={result['gap_vehicles']:.2f}%, gapc={result['gap_cost']:.2f}%")
                # --- KẾT THÚC SỬA ĐỔI ---

            except Exception as e:
                print(f"[ERROR] Error testing {instance_file}: {e}")
                import traceback
                traceback.print_exc() # In chi tiết lỗi để dễ debug
                continue
        
        # Save results
        self._save_results()
        
        # Generate comparison table
        self._generate_comparison_table()
        
        print("\n" + "="*80)
        print("BATCH TESTING COMPLETED")
        print("="*80)
    
    def _get_instance_files(self, max_instances: int = None) -> List[str]:
        """Get list of instance files to test from multiple directories"""
        instance_files = []
        
        # Directories to scan for instances
        search_dirs = [
            "../instances/n100/n100",  # n100 instances
            "../instances",             # Root instances folder
        ]
        
        # Scan all directories
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for file in os.listdir(search_dir):
                    if file.endswith('.txt') and not file.startswith('README'):
                        full_path = os.path.join(search_dir, file)
                        if full_path not in instance_files:
                            instance_files.append(full_path)
        
        # Sort by name for consistent ordering
        instance_files = sorted(instance_files)
        
        # Apply limit if specified
        if max_instances and max_instances > 0:
            instance_files = instance_files[:max_instances]
        
        return instance_files
    
    def _save_results(self):
        """Save results to JSON file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\nResults saved to: {self.results_file}")
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def _generate_comparison_table(self):
        """Generate comparison table grouped by dataset class"""
        if not self.results:
            print("No results to display")
            return
        
        # Group results by dataset type (bar, ber, nyc, poa)
        grouped_results = {}
        for result in self.results:
            # Skip failed results
            if result.get('status') == 'FAILED':
                continue
                
            instance_name = result['instance']
            # Extract dataset type (bar, ber, nyc, poa, etc.)
            dataset_type = instance_name.split('-')[0]
            
            if dataset_type not in grouped_results:
                grouped_results[dataset_type] = []
            grouped_results[dataset_type].append(result)
        
        print("\n" + "="*110)
        print("RESULTS COMPARISON TABLE - GROUPED BY DATASET")
        print("="*110)
        
        # Overall statistics
        all_results = [r for r in self.results if r.get('status') != 'FAILED']
        
        for dataset_type in sorted(grouped_results.keys()):
            results = grouped_results[dataset_type]
            
            print(f"\n{'='*110}")
            print(f"DATASET: {dataset_type.upper()}")
            print(f"{'='*110}")
            
            # Table header
            header = f"{'Instance':<18} {'Veh.':<6} {'Cost':<8} {'Gap_V(%)':<10} {'Gap_C(%)':<10} {'Time(s)':<8} {'BKS_Veh':<8} {'BKS_Cost':<10} {'Feasible':<10}"
            print(header)
            print("-"*110)
            
            # Results rows
            dataset_gap_vehicles = []
            dataset_gap_cost = []
            dataset_time = []
            
            for result in sorted(results, key=lambda x: x['instance']):
                instance_name = result['instance']
                vehicles = result['vehicles']
                cost = int(result['cost'])
                gap_vehicles = result['gap_vehicles']
                gap_cost = result['gap_cost']
                runtime = result['runtime']
                bk_vehicles = result.get('best_vehicles', '-')
                bk_cost = int(result.get('best_cost', 0)) if result.get('best_cost') else '-'
                feasible = 'YES' if result.get('is_feasible', False) else 'NO'
                
                row = f"{instance_name:<18} {vehicles:<6} {cost:<8} {gap_vehicles:<10.2f} {gap_cost:<10.2f} {runtime:<8.1f} {bk_vehicles:<8} {bk_cost:<10} {feasible:<10}"
                print(row)
                
                dataset_gap_vehicles.append(gap_vehicles)
                dataset_gap_cost.append(gap_cost)
                dataset_time.append(runtime)
            
            # Dataset summary
            if dataset_gap_vehicles:
                print("-"*110)
                avg_gap_v = sum(dataset_gap_vehicles) / len(dataset_gap_vehicles)
                avg_gap_c = sum(dataset_gap_cost) / len(dataset_gap_cost)
                avg_time = sum(dataset_time) / len(dataset_time)
                
                summary = f"{'AVG ' + dataset_type:<18} {'-':<6} {'-':<8} {avg_gap_v:<10.2f} {avg_gap_c:<10.2f} {avg_time:<8.1f}"
                print(summary)
        
        # Overall summary
        print("\n" + "="*110)
        print("OVERALL SUMMARY STATISTICS")
        print("="*110)
        
        if all_results:
            total_instances = len(all_results)
            avg_gap_vehicles = sum(r['gap_vehicles'] for r in all_results) / total_instances
            avg_gap_cost = sum(r['gap_cost'] for r in all_results) / total_instances
            avg_time = sum(r['runtime'] for r in all_results) / total_instances
            
            print(f"Total instances tested: {total_instances}")
            print(f"Feasible solutions: {sum(1 for r in all_results if r.get('is_feasible', False))}/{total_instances} ({100*sum(1 for r in all_results if r.get('is_feasible', False))/total_instances:.1f}%)")
            print(f"Average vehicle gap: {avg_gap_vehicles:.2f}%")
            print(f"Average cost gap: {avg_gap_cost:.2f}%")
            print(f"Average runtime: {avg_time:.1f}s")
            
            # Best results
            best_vehicle_gap = min(r['gap_vehicles'] for r in all_results)
            best_cost_gap = min(r['gap_cost'] for r in all_results)
            best_instance_v = min(all_results, key=lambda x: x['gap_vehicles'])['instance']
            best_instance_c = min(all_results, key=lambda x: x['gap_cost'])['instance']
            
            print(f"\nBest vehicle gap: {best_vehicle_gap:.2f}% ({best_instance_v})")
            print(f"Best cost gap: {best_cost_gap:.2f}% ({best_instance_c})")
            
            # Gap ranges
            gap_ranges = {
                '<10%': sum(1 for r in all_results if r['gap_cost'] < 10),
                '10-20%': sum(1 for r in all_results if 10 <= r['gap_cost'] < 20),
                '20-30%': sum(1 for r in all_results if 20 <= r['gap_cost'] < 30),
                '30-50%': sum(1 for r in all_results if 30 <= r['gap_cost'] < 50),
                '>50%': sum(1 for r in all_results if r['gap_cost'] >= 50)
            }
            
            print(f"\nCost Gap Distribution:")
            for range_name, count in gap_ranges.items():
                print(f"  {range_name}: {count}/{total_instances} ({100*count/total_instances:.1f}%)")
        
        print("="*110)


def main():
    """Main function to run batch testing"""
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        max_instances = int(sys.argv[1]) if sys.argv[1] != 'all' else None
    else:
        max_instances = None  # Run ALL instances by default
    
    if len(sys.argv) > 2:
        max_time = int(sys.argv[2])
    else:
        max_time = 60  # 60s per instance
    
    # Create batch tester
    tester = BatchTester()
    
    # Run batch test on available instances
    print(f"Configuration: max_instances={max_instances or 'ALL'}, max_time={max_time}s per instance")
    tester.run_batch_test(max_instances=max_instances, max_time_per_instance=max_time)


if __name__ == "__main__":
    main()
